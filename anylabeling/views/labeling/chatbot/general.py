from PyQt5.QtCore import Qt, QEasingCurve, QEvent, QTimer, QPropertyAnimation
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QFrame, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QSizePolicy, QTextEdit, QMessageBox
)

from anylabeling.views.labeling.chatbot.config import *
from anylabeling.views.labeling.chatbot.style import *
from anylabeling.views.labeling.chatbot.utils import *


class ChatMessage(QFrame):
    """Custom widget for a single chat message"""

    def __init__(self, role, content, parent=None, is_error=False):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.is_error = is_error
        self.is_editing = False
        self.resize_in_progress = False  # Flag to prevent recursion
        self.animation_min_height = 40
        self.edit_area_min_height = 80

        # Create message container with appropriate styling
        is_user = role == "user"

        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(0)

        # Create a horizontal layout to position the bubble
        h_container = QHBoxLayout()
        h_container.setContentsMargins(0, 0, 0, 0)
        h_container.setSpacing(0)

        # Create bubble with smooth corners
        self.bubble = QWidget(self)
        self.bubble.setObjectName("messageBubble")
        self.bubble.setStyleSheet(ChatMessageStyle.get_bubble_style(is_user))

        if is_user:
            h_container.addStretch(100 - USER_MESSAGE_MAX_WIDTH_PERCENT)
            h_container.addWidget(self.bubble, USER_MESSAGE_MAX_WIDTH_PERCENT)
        else:
            h_container.addWidget(self.bubble, 100)

        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(10, 8, 10, 8)
        bubble_layout.setSpacing(4)

        # Add header with role
        header_layout = QHBoxLayout()
        role_label = QLabel(self.tr("User") if is_user else self.tr("Assistant"))
        role_label.setStyleSheet(ChatMessageStyle.get_role_label_style())

        # Create copy button
        self.copy_btn = QPushButton()
        self.copy_btn.setIcon(QIcon(set_icon_path("copy")))
        self.copy_btn.setFixedSize(*ICON_SIZE_SMALL)
        self.copy_btn.setStyleSheet(ChatMessageStyle.get_button_style())
        self.copy_btn.setToolTip(self.tr("Copy"))
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.clicked.connect(lambda: self.copy_content_to_clipboard(self.copy_btn))
        self.copy_btn.setVisible(False)

        # Create delete button
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(set_icon_path("trash")))
        self.delete_btn.setFixedSize(*ICON_SIZE_SMALL)
        self.delete_btn.setStyleSheet(ChatMessageStyle.get_button_style())
        self.delete_btn.setToolTip(self.tr("Delete"))
        self.delete_btn.setCursor(Qt.PointingHandCursor)
        self.delete_btn.clicked.connect(self.confirm_delete_message)
        self.delete_btn.setVisible(False)

        self.edit_btn = None
        self.regenerate_btn = None
        if is_user:
            self.edit_btn = QPushButton()
            self.edit_btn.setIcon(QIcon(set_icon_path("edit")))
            self.edit_btn.setFixedSize(*ICON_SIZE_SMALL)
            self.edit_btn.setStyleSheet(ChatMessageStyle.get_button_style())
            self.edit_btn.setToolTip(self.tr("Edit"))
            self.edit_btn.setCursor(Qt.PointingHandCursor)
            self.edit_btn.clicked.connect(self.enter_edit_mode)
            self.edit_btn.setVisible(False)
            header_layout.addWidget(role_label)
        else:
            self.regenerate_btn = QPushButton()
            self.regenerate_btn.setIcon(QIcon(set_icon_path("refresh")))
            self.regenerate_btn.setFixedSize(*ICON_SIZE_SMALL)
            self.regenerate_btn.setStyleSheet(ChatMessageStyle.get_button_style())
            self.regenerate_btn.setToolTip(self.tr("Regenerate"))
            self.regenerate_btn.setCursor(Qt.PointingHandCursor)
            self.regenerate_btn.clicked.connect(self.regenerate_response)
            self.regenerate_btn.setVisible(False)
            header_layout.addWidget(role_label)

        bubble_layout.addLayout(header_layout)

        # Add message content
        processed_content = ""
        if len(content) > 50 and " " not in content:
            chunk_size = 50
            for i in range(0, len(content), chunk_size):
                processed_content += content[i:i+chunk_size]
                if i + chunk_size < len(content):
                    processed_content += "\u200B"  # Zero-width space, allows line breaks but is invisible
        else:
            processed_content = content

        # Create label with processed content
        content_label = QLabel(processed_content)
        content_label.setWordWrap(True)

        # Force minimum width to ensure correct wrapping
        content_label.setMinimumWidth(200)

        # To ensure long content displays correctly, we use RichText format
        if "\u200B" in processed_content or is_error:
            content_label.setTextFormat(Qt.RichText)
        else:
            content_label.setTextFormat(Qt.PlainText)

        content_label.setStyleSheet(ChatMessageStyle.get_content_label_style(self.is_error))

        # Add text copy selection combination flag
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

        # Use a more appropriate size policy to avoid excessive vertical space
        content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Ensure consistent font display across all platforms
        default_font = content_label.font()
        content_label.setFont(default_font)

        # Set alignment and minimum height to avoid excessive height
        content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        content_label.setMinimumHeight(10)
        self.content_label = content_label
        bubble_layout.addWidget(content_label)

        # Create a layout for the action buttons at the bottom right
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.setContentsMargins(0, 4, 0, 0)
        action_buttons_layout.setSpacing(4)

        # Add stretch to push buttons to the right
        action_buttons_layout.addStretch()

        # Add buttons to the bottom layout
        if is_user:
            action_buttons_layout.addWidget(self.copy_btn)
            action_buttons_layout.addWidget(self.edit_btn)
            action_buttons_layout.addWidget(self.delete_btn)
        else:
            action_buttons_layout.addWidget(self.copy_btn)
            action_buttons_layout.addWidget(self.regenerate_btn)
            action_buttons_layout.addWidget(self.delete_btn)

        # Store buttons for hover events
        self.action_buttons = [btn for btn in [self.copy_btn, self.edit_btn, self.regenerate_btn, self.delete_btn] if btn]

        # Add the action buttons layout to the bubble
        bubble_layout.addLayout(action_buttons_layout)

        # Create an edit area for user messages (hidden by default)
        self.edit_area = QTextEdit()
        self.edit_area.setPlainText(content)
        self.edit_area.setStyleSheet(ChatMessageStyle.get_content_label_style(False))
        self.edit_area.setFrameShape(QFrame.NoFrame)
        self.edit_area.setFrameShadow(QFrame.Plain)
        self.edit_area.setWordWrapMode(True)
        self.edit_area.setMinimumHeight(self.edit_area_min_height)
        self.edit_area.setVisible(False)
        bubble_layout.addWidget(self.edit_area)
        
        # Create buttons for edit mode (hidden by default)
        self.edit_buttons_widget = QWidget()
        edit_buttons_layout = QHBoxLayout(self.edit_buttons_widget)
        edit_buttons_layout.setContentsMargins(0, 8, 0, 0)
        edit_buttons_layout.setSpacing(8)

        # Add stretch to push buttons to the right
        edit_buttons_layout.addStretch()

        # Cancel button
        self.cancel_btn = QPushButton(self.tr("Cancel"))
        self.cancel_btn.setStyleSheet(ChatMessageStyle.get_cancel_button_style())
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.exit_edit_mode)

        # Save button
        self.save_btn = QPushButton(self.tr("Save"))
        self.save_btn.setStyleSheet(ChatMessageStyle.get_save_button_style())
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_edit)

        edit_buttons_layout.addWidget(self.cancel_btn)
        edit_buttons_layout.addWidget(self.save_btn)

        # Add edit buttons to bubble layout but keep hidden
        self.edit_buttons_widget.setStyleSheet(ChatMessageStyle.get_edit_button_wdiget_style())
        self.edit_buttons_widget.setVisible(False)
        bubble_layout.addWidget(self.edit_buttons_widget)

        self.bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        if parent:
            parent_width = parent.width()
            if parent_width > 0:
                # Different width constraints for user vs assistant
                if self.role == "user":
                    max_width = int(parent_width * USER_MESSAGE_MAX_WIDTH_PERCENT / 100)
                else:
                    max_width = int(parent_width)

                if max_width > 0:
                    if hasattr(self, 'content_label'):
                        self.content_label.setMaximumWidth(max_width - 20)
                    if hasattr(self, 'edit_area'):
                        self.edit_area.setMaximumWidth(max_width - 20)
                    self.bubble.setMaximumWidth(max_width)
                    if hasattr(self, 'content_label') and hasattr(self, 'adjust_height_after_animation'):
                        self.adjust_height_after_animation()
                    if self.is_editing and hasattr(self, 'adjust_height_during_edit'):
                        self.adjust_height_during_edit()

                    self.updateGeometry()
                    self.bubble.updateGeometry()

        layout.addLayout(h_container)

        # Add animation when first appearing
        self.setMaximumHeight(0)
        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(int(ANIMATION_DURATION[:-2]))  # Convert "200ms" to 200
        self.animation.setStartValue(0)

        content_height = self.content_label.sizeHint().height()
        bubble_height = content_height + (bubble_layout.contentsMargins().top() + 
                                         bubble_layout.contentsMargins().bottom() + 
                                         bubble_layout.spacing() + 
                                         30)
        
        # Set minimum height to avoid excessive height
        anim_end_height = max(self.animation_min_height, bubble_height)

        # Set end value and easing curve
        self.animation.setEndValue(anim_end_height)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # After animation, adjust height to a reasonable value
        self.animation.finished.connect(self.adjust_height_after_animation)

        self.animation.start()

    def copy_content_to_clipboard(self, button):
        """Copy message content to clipboard with visual feedback"""
        # Copy the content to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.content)

        # Change the button icon to a checkmark
        button.setIcon(QIcon(set_icon_path("check")))

        # Start a timer to reset the button after a delay
        QTimer.singleShot(1000, lambda: self.reset_copy_button(button))

    def update_width_constraint(self):
        """Update width constraint based on parent width"""
        # Prevent recursion
        if self.resize_in_progress:
            return
            
        self.resize_in_progress = True
        try:
            if self.parent():
                parent_width = self.parent().width()
                if parent_width > 0:
                    if self.role == "user":
                        max_width = int(parent_width * USER_MESSAGE_MAX_WIDTH_PERCENT / 100)
                    else:
                        max_width = int(parent_width)

                    if max_width > 0:
                        if hasattr(self, 'content_label'):
                            self.content_label.setMaximumWidth(max_width - 20)
                        
                        if hasattr(self, 'edit_area'):
                            self.edit_area.setMaximumWidth(max_width - 20)

                        self.bubble.setMaximumWidth(max_width)

                        if hasattr(self, 'content_label') and hasattr(self, 'adjust_height_after_animation'):
                            if not self.is_editing:
                                self.adjust_height_after_animation()
                        
                        self.updateGeometry()
                        self.bubble.updateGeometry()
        finally:
            self.resize_in_progress = False

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        # Only update width constraint if not already in progress
        if not self.resize_in_progress:
            self.update_width_constraint()

    def reset_copy_button(self, button):
        """Reset the copy button to its original state"""
        button.setIcon(QIcon(set_icon_path("copy")))
        button.setToolTip(self.tr("Copy"))
        button.setStyleSheet(ChatMessageStyle.get_button_style())

    def adjust_height_after_animation(self):
        """Adjust height after animation"""
        # Prevent recursion
        if self.resize_in_progress:
            return
            
        self.resize_in_progress = True
        try:
            # Get the actual height needed for the content
            content_height = self.content_label.heightForWidth(self.content_label.width())
            # If the height cannot be obtained correctly, use sizeHint
            if content_height <= 0:
                content_height = self.content_label.sizeHint().height()
            
            # Add extra space for the header and padding
            total_height = content_height + self.animation_min_height
            
            # Set a reasonable maximum height, slightly larger than the calculated height
            self.setMaximumHeight(total_height + 10)
        finally:
            self.resize_in_progress = False

    def enter_edit_mode(self):
        """Enter edit mode for user messages"""
        if self.role != "user":
            return
            
        self.is_editing = True
        
        # Hide the normal content and show the edit area
        self.content_label.setVisible(False)
        self.edit_area.setVisible(True)
        self.edit_area.setPlainText(self.content)
        self.edit_buttons_widget.setVisible(True)
        
        # Set focus to the edit area
        self.edit_area.setFocus()
        
        # Adjust the widget height
        self.adjust_height_during_edit()
    
    def exit_edit_mode(self):
        """Exit edit mode without saving changes"""
        self.is_editing = False
        
        # Show the normal content and hide the edit area
        self.content_label.setVisible(True)
        self.edit_area.setVisible(False)
        self.edit_buttons_widget.setVisible(False)
        
        # Reset the edit area text
        self.edit_area.setPlainText(self.content)
        
        # Adjust the widget height
        self.adjust_height_after_animation()
    
    def save_edit(self):
        """Save edited content and resubmit the message"""
        # Get edited content
        edited_content = self.edit_area.toPlainText().strip()
        
        # Only proceed if content has changed and is not empty
        if edited_content and edited_content != self.content:
            # Get the dialog
            dialog = self.window()
            if hasattr(dialog, 'clear_messages_after') and hasattr(dialog, 'message_input'):
                # Exit edit mode first to return to normal view
                self.is_editing = False
                self.content_label.setVisible(True)
                self.edit_area.setVisible(False)
                self.edit_buttons_widget.setVisible(False)
                
                # Call the dialog method to handle deletion and resubmission
                dialog.resubmit_edited_message(self, edited_content)
            else:
                # Just update the content if we can't find the dialog methods
                self.content = edited_content
                self.content_label.setText(edited_content)
                self.exit_edit_mode()
        else:
            # No changes or empty content, just exit edit mode
            self.exit_edit_mode()
    
    def adjust_height_during_edit(self):
        """Adjust widget height during edit mode"""
        # Prevent recursion
        if self.resize_in_progress:
            return
            
        self.resize_in_progress = True
        try:
            # Get the height needed for the edit area
            edit_height = self.edit_area.document().size().height() + 20
            buttons_height = self.edit_buttons_widget.sizeHint().height() + 10
            
            # Calculate total height needed
            total_height = edit_height + buttons_height + self.edit_area_min_height

            # Set a reasonable height for the edit mode
            self.setMaximumHeight(total_height + 20)
            
            # Force update layout
            self.updateGeometry()
            QApplication.processEvents()
        finally:
            self.resize_in_progress = False

    def regenerate_response(self):
        """Regenerate the assistant's response"""
        dialog = self.window()
        if hasattr(dialog, 'regenerate_response'):
            dialog.regenerate_response(self)

    def confirm_delete_message(self):
        """Show confirmation dialog before deleting message"""
        # Create confirmation dialog
        confirm_dialog = QMessageBox(self.window())
        confirm_dialog.setText(self.tr("Are you sure to delete this message forever?"))
        confirm_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_dialog.setDefaultButton(QMessageBox.No)
        confirm_dialog.setIcon(QMessageBox.Warning)

        # Show dialog and handle response
        response = confirm_dialog.exec_()
        if response == QMessageBox.Yes:
            self.delete_message()

    def delete_message(self):
        """Delete this message and update chat history"""
        # Find the main dialog
        dialog = self.window()

        # Find this message's index in the chat messages layout
        message_widgets = []
        for i in range(dialog.chat_messages_layout.count()):
            item = dialog.chat_messages_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), ChatMessage):
                message_widgets.append(item.widget())

        if self in message_widgets:
            message_index = message_widgets.index(self)

            # Remove this message from the layout
            dialog.chat_messages_layout.removeWidget(self)

            # Update chat history
            if hasattr(dialog, 'chat_history') and 0 <= message_index < len(dialog.chat_history):
                dialog.chat_history.pop(message_index)

                # If this is a file-based chat, update the stored data
                if hasattr(dialog, 'parent') and callable(dialog.parent) and dialog.parent():
                    parent = dialog.parent()
                    if hasattr(parent, 'other_data') and hasattr(parent, 'filename'):
                        if parent.filename and 'chat_history' in parent.other_data:
                            parent.other_data['chat_history'] = dialog.chat_history
                            # Mark as dirty to ensure changes are saved
                            if hasattr(parent, 'set_dirty'):
                                parent.set_dirty()

            # Delete the widget
            self.setParent(None)
            self.deleteLater()

    # Add mouse hover events to show/hide buttons
    def enterEvent(self, event):
        """Show action buttons when mouse enters the message"""
        # First make buttons visible
        for button in self.action_buttons:
            button.setVisible(True)

        # Then adjust bubble height to accommodate the buttons
        self.adjust_height_for_buttons(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hide action buttons when mouse leaves the message"""
        # First hide buttons
        for button in self.action_buttons:
            button.setVisible(False)

        # Then restore original height
        self.adjust_height_for_buttons(False)
        super().leaveEvent(event)

    def adjust_height_for_buttons(self, show_buttons):
        """Adjust the message height when buttons appear/disappear"""
        # Prevent recursion
        if self.resize_in_progress:
            return

        self.resize_in_progress = True
        try:
            # Get the actual height needed for the content
            content_height = self.content_label.heightForWidth(self.content_label.width())
            if content_height <= 0:
                content_height = self.content_label.sizeHint().height()

            # Add extra space for the header and padding
            total_height = content_height + self.animation_min_height

            # Add extra space for buttons if they're showing
            if show_buttons:
                # Get button height + padding
                button_space = 30  # Typical button height + padding
                total_height += button_space

            # Set the maximum height with a small buffer
            self.setMaximumHeight(total_height + 10)
            
            # Force update
            self.updateGeometry()
            self.bubble.updateGeometry()
            QApplication.processEvents()
        finally:
            self.resize_in_progress = False


class UpdateModelsEvent(QEvent):
    """Custom event for updating models dropdown"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self, models):
        super().__init__(self.EVENT_TYPE)
        self.models = models


class EnableRefreshButtonEvent(QEvent):
    """Custom event for enabling refresh button"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self):
        super().__init__(self.EVENT_TYPE)

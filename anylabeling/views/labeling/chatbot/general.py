from PyQt5.QtCore import (
    QPoint,
    QEvent,
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    Qt,
    pyqtSignal,
)
from PyQt5.QtGui import QIcon, QPixmap, QTextCursor
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QTextEdit,
)

from anylabeling.views.labeling.chatbot.config import *
from anylabeling.views.labeling.chatbot.style import *
from anylabeling.views.labeling.chatbot.utils import *


class BatchProcessDialog(QDialog):
    """Batch processing dialog class"""
    promptReady = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(self.tr("Batch Process All Images"))
        self.setMinimumWidth(450)
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI interface"""
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 8px;
            }
        """)

        # Main layout
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(24, 24, 24, 24)
        dialog_layout.setSpacing(20)

        # Instruction label
        instruction_label = QLabel(self.tr("Enter the prompt to apply to all images:"))
        instruction_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #374151;
                font-weight: 500;
            }
        """)
        dialog_layout.addWidget(instruction_label)

        # Input box design
        self.batch_message_input = QTextEdit()
        self.batch_message_input.setPlaceholderText(
            self.tr("Type your prompt here and use `@image` to reference the image.")
        )
        self.batch_message_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                background-color: #F9FAFB;
                color: #1F2937;
                font-size: 14px;
                line-height: 1.5;
                padding: 12px;
            }
            QTextEdit:focus {
                border: 1px solid #6366F1;
            }
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #D1D5DB;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        self.batch_message_input.setAcceptRichText(False)
        self.batch_message_input.setMinimumHeight(160)
        self.batch_message_input.setMaximumHeight(200)
        self.batch_message_input.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        dialog_layout.addWidget(self.batch_message_input)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.setSpacing(12)
        button_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton(self.tr("Cancel"))
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #4B5563;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #D1D5DB;
            }
            QPushButton:pressed {
                background-color: #F3F4F6;
            }
        """)
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        # Confirm button
        confirm_btn = QPushButton(self.tr("Confirm"))
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F46E5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4338CA;
            }
            QPushButton:pressed {
                background-color: #3730A3;
            }
        """)
        confirm_btn.setMinimumHeight(36)
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.clicked.connect(self.accept)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(confirm_btn)
        dialog_layout.addLayout(button_layout)

        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setWindowFlags(self.windowFlags() & ~Qt.FramelessWindowHint)

    def center_on_parent(self):
        """Center the dialog on the parent window"""
        if self.parent:
            center_point = self.parent.mapToGlobal(self.parent.rect().center())
            dialog_rect = self.rect()
            self.move(center_point.x() - dialog_rect.width() // 2, 
                      center_point.y() - dialog_rect.height() // 2)

    def get_prompt(self):
        """Get the user input prompt"""
        return self.batch_message_input.toPlainText().strip()

    def exec_(self):
        """Override exec_ method to adjust position before showing the dialog"""
        self.adjustSize()
        self.center_on_parent()
        result = super().exec_()

        if result == QDialog.Accepted:
            prompt = self.get_prompt()
            if prompt:
                self.promptReady.emit(prompt)
                return prompt
        return ""


class ChatMessage(QFrame):
    """Custom widget for a single chat message"""

    def __init__(self, role, content, provider, parent=None, is_error=False):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.provider = provider
        self.is_error = is_error
        self.is_editing = False
        self.resize_in_progress = False  # Flag to prevent recursion
        self.animation_min_height = 40
        self.edit_area_min_height = 80

        # Enable context menu policy for the frame
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Create message container with appropriate styling
        is_user = role == "user"

        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
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
            # h_container.addStretch()

        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(10, 8, 10, 8)
        bubble_layout.setSpacing(4)

        # Add header with role
        if not is_user:
            header_layout = QHBoxLayout()
            icon_container = QFrame()
            icon_container.setObjectName("roleLabelContainer")
            icon_container.setStyleSheet(ChatMessageStyle.get_role_label_background_style())
            icon_container_layout = QHBoxLayout(icon_container)
            icon_container_layout.setContentsMargins(2, 2, 2, 2)
            icon_container_layout.setSpacing(0)

            role_label = QLabel()
            icon_pixmap = QPixmap(set_icon_path(self.provider))
            scaled_icon = icon_pixmap.scaled(*ICON_SIZE_SMALL, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            role_label.setPixmap(scaled_icon)
            role_label.setStyleSheet(ChatMessageStyle.get_role_label_style())

            icon_container_layout.addWidget(role_label)
            header_layout.addWidget(icon_container)
            header_layout.addStretch()
            bubble_layout.addLayout(header_layout)

        # Create custom tooltips
        self.copy_tooltip = CustomTooltip(title="Copy")
        self.delete_tooltip = CustomTooltip(title="Delete")
        
        if is_user:
            self.edit_tooltip = CustomTooltip(title="Edit")
        else:
            self.regenerate_tooltip = CustomTooltip(title="Regenerate")
            self.edit_tooltip = CustomTooltip(title="Edit")

        # Create copy button
        self.copy_btn = QPushButton()
        self.copy_btn.setIcon(QIcon(set_icon_path("copy")))
        self.copy_btn.setFixedSize(*ICON_SIZE_SMALL)
        self.copy_btn.setStyleSheet(ChatMessageStyle.get_button_style())
        self.copy_btn.clicked.connect(lambda: self.copy_content_to_clipboard(self.copy_btn))
        self.copy_btn.setVisible(False)
        self.copy_btn.installEventFilter(self)
        self.copy_btn.setObjectName("copy_btn")

        # Create delete button
        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon(set_icon_path("trash")))
        self.delete_btn.setFixedSize(*ICON_SIZE_SMALL)
        self.delete_btn.setStyleSheet(ChatMessageStyle.get_button_style())
        self.delete_btn.clicked.connect(self.confirm_delete_message)
        self.delete_btn.setVisible(False)
        self.delete_btn.installEventFilter(self)
        self.delete_btn.setObjectName("delete_btn")

        self.edit_btn = None
        self.regenerate_btn = None
        if is_user:
            # Create edit button
            self.edit_btn = QPushButton()
            self.edit_btn.setIcon(QIcon(set_icon_path("edit")))
            self.edit_btn.setFixedSize(*ICON_SIZE_SMALL)
            self.edit_btn.setStyleSheet(ChatMessageStyle.get_button_style())
            self.edit_btn.clicked.connect(self.enter_edit_mode)
            self.edit_btn.setVisible(False)
            self.edit_btn.installEventFilter(self)
            self.edit_btn.setObjectName("edit_btn")
        else:
            # Create regenerate button
            self.regenerate_btn = QPushButton()
            self.regenerate_btn.setIcon(QIcon(set_icon_path("refresh")))
            self.regenerate_btn.setFixedSize(*ICON_SIZE_SMALL)
            self.regenerate_btn.setStyleSheet(ChatMessageStyle.get_button_style())
            self.regenerate_btn.clicked.connect(self.regenerate_response)
            self.regenerate_btn.setVisible(False)
            self.regenerate_btn.installEventFilter(self)
            self.regenerate_btn.setObjectName("regenerate_btn")

            # Create edit button
            self.edit_btn = QPushButton()
            self.edit_btn.setIcon(QIcon(set_icon_path("edit")))
            self.edit_btn.setFixedSize(*ICON_SIZE_SMALL)
            self.edit_btn.setStyleSheet(ChatMessageStyle.get_button_style())
            self.edit_btn.clicked.connect(self.enter_edit_mode)
            self.edit_btn.setVisible(False)
            self.edit_btn.installEventFilter(self)
            self.edit_btn.setObjectName("edit_btn")

        # Add message content
        processed_content = self._process_content(content)

        # Create label with processed content
        content_label = self._create_content_label(processed_content)

        # Use a more appropriate size policy to avoid excessive vertical space
        content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Set alignment and minimum height to avoid excessive height
        if self.role == "user":
            content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        content_label.setMinimumHeight(10)
        self.content_label = content_label
        bubble_layout.addWidget(content_label)

        # Create a layout for the action buttons at the bottom right
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.setContentsMargins(0, 4, 0, 0)
        action_buttons_layout.setSpacing(12)

        # Set a container for the action buttons
        buttons_container = QWidget()
        buttons_container.setMinimumHeight(20)
        buttons_container.setStyleSheet("background-color: transparent;")
        buttons_container.setLayout(action_buttons_layout)
        bubble_layout.addWidget(buttons_container)

        # Add stretch to push buttons to the right
        action_buttons_layout.addStretch()

        # Add buttons to the bottom layout
        if is_user:
            action_buttons_layout.addWidget(self.copy_btn)
            action_buttons_layout.addWidget(self.edit_btn)
            action_buttons_layout.addWidget(self.delete_btn)
        else:
            action_buttons_layout.addWidget(self.copy_btn)
            action_buttons_layout.addWidget(self.edit_btn)
            action_buttons_layout.addWidget(self.regenerate_btn)
            action_buttons_layout.addWidget(self.delete_btn)

        # Store buttons for hover events
        self.action_buttons = [btn for btn in [
            self.copy_btn, self.edit_btn, self.regenerate_btn, self.delete_btn] if btn]

        # Create an edit area for user messages (hidden by default)
        self.edit_area = QTextEdit()
        self.edit_area.setPlainText(content)
        self.edit_area.setStyleSheet(ChatMessageStyle.get_edit_area_style())
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

        # Resend button
        self.resend_btn = QPushButton(self.tr("Resend"))
        self.resend_btn.setStyleSheet(ChatMessageStyle.get_resend_button_style())
        self.resend_btn.clicked.connect(self.resend_message)
        edit_buttons_layout.addWidget(self.resend_btn)
        edit_buttons_layout.addStretch()

        # Cancel button
        self.cancel_btn = QPushButton(self.tr("Cancel"))
        self.cancel_btn.setStyleSheet(ChatMessageStyle.get_cancel_button_style())
        self.cancel_btn.clicked.connect(self.exit_edit_mode)

        # Save button
        self.save_btn = QPushButton(self.tr("Save"))
        self.save_btn.setStyleSheet(ChatMessageStyle.get_save_button_style())
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
        self.animation.setDuration(int(ANIMATION_DURATION[:-2]))
        self.animation.setStartValue(0)

        content_height = self.content_label.sizeHint().height()
        bubble_height = content_height + (bubble_layout.contentsMargins().top() + 
                                         bubble_layout.contentsMargins().bottom() + 
                                         bubble_layout.spacing() + 
                                         30)

        # Set end value and easing curve
        anim_end_height = max(self.animation_min_height, bubble_height)
        self.animation.setEndValue(anim_end_height)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        # After animation, adjust height to a reasonable value
        self.animation.finished.connect(self.adjust_height_after_animation)
        self.animation.start()

    def _process_content(self, content):
        """Process message content for better display handling"""
        if len(content) > 50 and " " not in content:
            chunk_size = 50
            processed_content = ""
            for i in range(0, len(content), chunk_size):
                processed_content += content[i:i+chunk_size]
                if i + chunk_size < len(content):
                    processed_content += "\u200B"  # Zero-width space, allows line breaks but is invisible
            return processed_content
        return content

    def _create_content_label(self, processed_content):
        """Create and configure the content label for the message"""
        if self.role == "user":
            content_label = QLabel(processed_content)
            content_label.setWordWrap(True)
            content_label.setMinimumWidth(200)
            
            # Set text format based on content
            if "\u200B" in processed_content or self.is_error:
                content_label.setTextFormat(Qt.RichText)
            else:
                content_label.setTextFormat(Qt.PlainText)
            
            content_label.setStyleSheet(ChatMessageStyle.get_content_label_style(self.is_error))
            content_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
            content_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            # Ensure consistent font display
            default_font = content_label.font()
            content_label.setFont(default_font)
            
            content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            content_label.setMinimumHeight(10)
            
            return content_label
        
        # For assistant messages, use QWebEngineView to render markdown
        else:
            web_view = QWebEngineView()
            web_view.setMinimumWidth(200)
            web_view.setMinimumHeight(10)
            web_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
            web_view.loadFinished.connect(lambda ok: self.adjust_height_after_animation() if ok else None)
            web_view.setHtml(set_html_style(processed_content))
            return web_view

    def set_action_buttons_enabled(self, enabled):
        """Enable or disable all action buttons"""
        for button in self.action_buttons:
            button.setEnabled(enabled)

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

    def copy_content_to_clipboard(self, button = None):
        """Copy message content to clipboard with visual feedback"""
        # Copy the content to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.content)

        # Change the button icon to a checkmark
        if button:
            button.setIcon(QIcon(set_icon_path("check")))

            # Start a timer to reset the button after a delay
            QTimer.singleShot(1000, lambda: self.reset_copy_button(button))

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
            if isinstance(self.content_label, QWebEngineView):
                self.content_label.page().runJavaScript(
                    "document.body.scrollHeight;",
                    self.apply_webview_height
                )
                return

            content_height = self.content_label.heightForWidth(self.content_label.width())
            # If the height cannot be obtained correctly, use sizeHint
            if content_height <= 0:
                content_height = self.content_label.sizeHint().height()

            # Add extra space for the header, padding and buttons (even when not visible)
            button_space = 40
            padding_space = 20
            total_height = content_height + self.animation_min_height + button_space + padding_space

            # Set a reasonable maximum height with some buffer
            self.setMaximumHeight(total_height)

            # Force update
            self.updateGeometry()
            QApplication.processEvents()
        finally:
            self.resize_in_progress = False

    def apply_webview_height(self, height):
        """(Callback func) Apply the height from JavaScript"""
        if not isinstance(self.content_label, QWebEngineView) or self.resize_in_progress:
            return
        
        try:
            self.resize_in_progress = True
            
            # Ensure height is a valid value
            if height and height > 0:
                button_space = self.edit_buttons_widget.sizeHint().height()
                total_height = height + self.animation_min_height + button_space
                self.content_label.setFixedHeight(height)
                self.setMaximumHeight(total_height)

                self.updateGeometry()
                self.bubble.updateGeometry()
                QApplication.processEvents()
        finally:
            self.resize_in_progress = False

    def enter_edit_mode(self):
        """Enter edit mode for chat messages"""
        # Hide the normal content
        self.content_label.setVisible(False)
        self.copy_btn.setVisible(False)
        self.edit_btn.setVisible(False)
        self.delete_btn.setVisible(False)

        # Hide regenerate button if it exists (for assistant messages)
        if hasattr(self, 'regenerate_btn') and self.regenerate_btn:
            self.regenerate_btn.setVisible(False)

        # Show the edit area
        self.edit_area.setVisible(True)
        self.edit_area.setPlainText(self.content)
        self.edit_area.setFocus()
        self.edit_area.moveCursor(QTextCursor.End)
        self.edit_buttons_widget.setVisible(True)

        # Hide the Resend button for assistant messages
        if self.role != "user":
            self.resend_btn.setVisible(False)
        else:
            self.resend_btn.setVisible(True)

        # Set the editing flag and adjust the widget height
        self.is_editing = True
        self.adjust_height_during_edit()

    def save_edit(self):
        """Save edited content only if it has changed"""
        edited_content = self.edit_area.toPlainText().strip()

        # Only proceed if content is not empty
        if edited_content:
            self.content = edited_content
            if isinstance(self.content_label, QLabel):
                self.content_label.setText(edited_content)
            else:
                self.content_label.setHtml(set_html_style(edited_content))

            dialog = self.window()

            # Find this message's index in the chat messages layout
            message_widgets = []
            for i in range(dialog.chat_messages_layout.count()):
                item = dialog.chat_messages_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), ChatMessage):
                    message_widgets.append(item.widget())

            if self in message_widgets:
                message_index = message_widgets.index(self)

                # Update chat history at this index
                if hasattr(dialog, 'chat_history') and 0 <= message_index < len(dialog.chat_history):
                    dialog.chat_history[message_index]['content'] = edited_content

                    # If this is a file-based chat, update the stored data
                    if hasattr(dialog, 'parent') and callable(dialog.parent) and dialog.parent():
                        parent = dialog.parent()
                        if hasattr(parent, 'other_data') and hasattr(parent, 'filename'):
                            if parent.filename:
                                parent.other_data['chat_history'] = dialog.chat_history
                                parent.set_dirty()

        self.exit_edit_mode()

    def exit_edit_mode(self):
        """Exit edit mode without saving changes"""
        # Show the normal content and hide the edit area
        self.content_label.setVisible(True)
        self.edit_area.setVisible(False)
        self.edit_buttons_widget.setVisible(False)

        # Reset the edit area text
        self.edit_area.setPlainText(self.content)

        # Set the editing flag and adjust the widget height
        self.is_editing = False
        self.adjust_height_after_animation()
    
    def resend_message(self):
        """Save edited content and resubmit the message"""
        edited_content = self.edit_area.toPlainText().strip()

        # Only proceed if content has changed and is not empty
        if edited_content and edited_content != self.content:
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
                            parent.set_dirty()

            # Delete the widget
            self.setParent(None)
            self.deleteLater()

    def enterEvent(self, event):
        """Show action buttons when mouse enters the message"""
        if self.is_editing:
            return

        for button in self.action_buttons:
            button.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hide action buttons when mouse leaves the message"""
        if self.is_editing:
            return

        for button in self.action_buttons:
            button.setVisible(False)
        super().leaveEvent(event)

    def eventFilter(self, obj, event):
        """Event filter for handling custom tooltips"""
        # Map button object names to their tooltips
        tooltip_buttons = {
            "copy_btn": self.copy_tooltip,
            "delete_btn": self.delete_tooltip,
        }
        
        if hasattr(self, "edit_btn") and self.edit_btn:
            tooltip_buttons["edit_btn"] = self.edit_tooltip
        
        if hasattr(self, "regenerate_btn") and self.regenerate_btn:
            tooltip_buttons["regenerate_btn"] = self.regenerate_tooltip
        
        # Handle tooltip display
        for btn_name, tooltip in tooltip_buttons.items():
            if obj.objectName() == btn_name:
                if event.type() == QEvent.Enter:
                    # Get button geometry
                    button_pos = obj.mapToGlobal(QPoint(0, 0))
                    button_width = obj.width()
                    button_height = obj.height()
                    
                    # Show tooltip first to ensure proper size calculation
                    tooltip.show()
                    tooltip.adjustSize()
                    
                    # Get tooltip dimensions
                    tooltip_width = tooltip.width()
                    tooltip_height = tooltip.height()
                    
                    # Calculate position centered above the button
                    target_x = button_pos.x() + (button_width - tooltip_width) // 2
                    target_y = button_pos.y() - tooltip_height - 5
                    
                    # Ensure tooltip stays within screen boundaries
                    screen = QApplication.desktop().screenGeometry()
                    if target_x + tooltip_width > screen.width():
                        target_x = screen.width() - tooltip_width - 5
                    if target_x < 0:
                        target_x = 5
                    if target_y < 0:
                        # If not enough space above, show below the button
                        target_y = button_pos.y() + button_height + 5
                    
                    tooltip.move(target_x, target_y)
                    return True
                elif event.type() == QEvent.Leave or event.type() == QEvent.Wheel:
                    tooltip.hide()
                    return True

        return False  # Let the event continue to be processed

    def show_context_menu(self, position):
        """Show custom context menu for the message bubble"""
        context_menu = QMenu(self)
        context_menu.setStyleSheet(ChatbotDialogStyle.get_menu_style())

        copy_action = context_menu.addAction(self.tr("Copy message"))
        copy_action.triggered.connect(lambda: self.copy_content_to_clipboard(None))
        context_menu.addSeparator()

        edit_action = context_menu.addAction(self.tr("Edit message"))
        edit_action.triggered.connect(self.enter_edit_mode)

        # Only add regenerate for assistant messages
        if self.role != "user":
            regenerate_action = context_menu.addAction(self.tr("Regenerate response"))
            regenerate_action.triggered.connect(self.regenerate_response)

        context_menu.addSeparator()
        delete_action = context_menu.addAction(self.tr("Delete message"))
        delete_action.triggered.connect(self.confirm_delete_message)

        context_menu.exec_(self.mapToGlobal(position))


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

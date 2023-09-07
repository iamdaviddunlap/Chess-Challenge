import sys
import threading
from PyQt5.QtWidgets import QScrollArea, QApplication, QWidget, QLabel, QVBoxLayout, qApp
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import matplotlib.cm as cm
import matplotlib.colors as colors

# Global variable to store the current thread
current_thread = None
# Flag to indicate if the thread should terminate
terminate_thread = False


def gui_thread(legal_moves_evaluation, cmap_name):
    global terminate_thread
    app = QApplication(sys.argv)

    # Set up a timer to check the termination flag every 500 ms
    timer = QTimer()
    timer.timeout.connect(lambda: check_terminate(app))
    timer.start(500)

    # Create the main window
    main_window = QWidget()
    main_window.setWindowTitle("Chess Moves Evaluation")
    main_layout = QVBoxLayout()
    main_window.setLayout(main_layout)

    scroll_area = QScrollArea(main_window)
    scroll_area.setWidgetResizable(True)
    content_widget = QWidget()
    layout = QVBoxLayout()
    content_widget.setLayout(layout)
    layout.setSpacing(0)
    scroll_area.setWidget(content_widget)
    main_layout.addWidget(scroll_area)

    cmap = cm.get_cmap(cmap_name)
    norm = colors.Normalize(vmin=min(legal_moves_evaluation.values()), vmax=max(legal_moves_evaluation.values()))

    font = QFont("Arial", 10)
    font.setBold(True)

    for key, value in legal_moves_evaluation.items():
        rgba = cmap(norm(value))
        hex_color = colors.to_hex(rgba)

        container = QWidget()
        container.setStyleSheet(f"background-color: {hex_color};")
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)

        label = QLabel(key)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(font)
        label.setStyleSheet("padding: 10px 0;")

        container_layout.addWidget(label)
        layout.addWidget(container)

    main_window.setFixedHeight(400)
    main_window.show()

    sys.exit(app.exec_())


def check_terminate(app):
    """Check if the terminate flag is set and exit the app if true."""
    global terminate_thread
    if terminate_thread:
        app.exit()


def display_move_evaluation(legal_moves_evaluation, cmap_name='Blues'):
    global current_thread, terminate_thread
    # If the thread is alive, set the termination flag
    if current_thread and current_thread.is_alive():
        terminate_thread = True
        current_thread.join()  # wait for the thread to finish

    terminate_thread = False  # Reset the flag
    current_thread = threading.Thread(target=gui_thread, args=(legal_moves_evaluation, cmap_name))
    current_thread.start()


# Example Usage
if __name__ == "__main__":
    legal_moves_evaluation = {"Move1": 0.2, "Move2": 0.5, "Move3": 0.8, "Move4": 0.1}
    display_move_evaluation(legal_moves_evaluation)
    print("This will print immediately after the window is shown.")

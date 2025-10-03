from core.sep import Sep
from ui.gui import qt
from ui.gui.config.layout import MARGINS, SPACING, APP_NAME

from .right_panel import RightPanel
from .sidebar import Sidebar


class MainWindow(qt.QWidget):
    def __init__(self):
        super().__init__()
        self.sep = Sep()
        self.setMinimumSize(800, 400)
        self.setWindowTitle(APP_NAME)
        self.init_ui()

    def init_ui(self):
        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(*MARGINS)
        layout.setSpacing(SPACING)

        splitter = qt.QSplitter(qt.Qt.Orientation.Horizontal)

        self.sidebar = Sidebar(self.sep)
        self.right_panel = RightPanel(self.sep)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.right_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

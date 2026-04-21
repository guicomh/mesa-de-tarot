import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget,
    QHBoxLayout, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QPixmap, QDrag
from PyQt5.QtCore import Qt, QMimeData


# 🧠 APP PRINCIPAL
class App(QWidget):
    def __init__(self):
        super().__init__()

        self.slots = []

        main_layout = QHBoxLayout()

        # =========================
        # 📌 GRID DAS CARTAS (ESQUERDA)
        # =========================
        grid_widget = QWidget()
        grid_layout = QGridLayout()

        pasta_cartas = "cartas"

        # 🔥 ORDENAÇÃO NUMÉRICA CORRETA
        imagens = sorted(
            os.listdir(pasta_cartas),
            key=lambda x: int(''.join(filter(str.isdigit, x)) or 0)
        )

        colunas = 3
        linha = 0
        coluna = 0

        for img in imagens:
            caminho = os.path.join(pasta_cartas, img)

            if caminho.endswith((".png", ".jpg", ".jpeg")):
                carta = CartaLabel(caminho, self)
                grid_layout.addWidget(carta, linha, coluna)

                coluna += 1
                if coluna >= colunas:
                    coluna = 0
                    linha += 1

        grid_widget.setLayout(grid_layout)

        scroll = QScrollArea()
        scroll.setWidget(grid_widget)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(350)

        # =========================
        # 🔮 TIRAGEM (DIREITA)
        # =========================
        tiragem_layout = QGridLayout()

        self.carta1 = DropArea("Carta 1")
        self.carta2 = DropArea("Carta 2")
        self.carta3 = DropArea("Carta 3")
        self.fundo = DropArea("Fundo")

        self.slots = [self.carta1, self.carta2, self.carta3, self.fundo]

        tiragem_layout.addWidget(self.carta1, 0, 0)
        tiragem_layout.addWidget(self.carta2, 0, 1)
        tiragem_layout.addWidget(self.carta3, 0, 2)
        tiragem_layout.addWidget(self.fundo, 1, 1)

        tiragem_layout.setHorizontalSpacing(60)
        tiragem_layout.setVerticalSpacing(60)

        container = QWidget()
        container.setLayout(tiragem_layout)

        # =========================
        # 📦 JUNTA TUDO
        # =========================
        main_layout.addWidget(scroll)
        main_layout.addWidget(container)

        self.setLayout(main_layout)
        self.setWindowTitle("Simulador Tarot")
        self.resize(1200, 700)

    # 🔥 colocar automaticamente
    def colocar_carta(self, image_path):
        for slot in self.slots:
            if slot.pixmap() is None:
                pixmap = QPixmap(image_path)
                slot.setPixmap(pixmap.scaled(220, 320, Qt.KeepAspectRatio))
                return


# 🃏 CARTA
class CartaLabel(QLabel):
    def __init__(self, image_path, app):
        super().__init__()
        self.image_path = image_path
        self.app = app

        pixmap = QPixmap(image_path)

        self.setPixmap(pixmap.scaled(90, 130, Qt.KeepAspectRatio))
        self.setFixedSize(90, 130)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.image_path)
            drag.setMimeData(mime)
            drag.setPixmap(self.pixmap())
            drag.exec_(Qt.MoveAction)

    # 🖱️ BOTÃO ESQUERDO → COLOCA AUTOMÁTICO
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.app.colocar_carta(self.image_path)


# 📌 DROP AREA
class DropArea(QLabel):
    def __init__(self, title):
        super().__init__(title)
        self.title = title
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)

        self.setFixedSize(220, 320)

        self.setStyleSheet("""
            border: 2px dashed gray;
            font-size: 14px;
        """)

        # 🔥 SOMBRA APENAS NA CARTA FUNDO
        if self.title == "Fundo":
            sombra = QGraphicsDropShadowEffect()
            sombra.setBlurRadius(40)   # intensidade
            sombra.setXOffset(0)
            sombra.setYOffset(10)      # efeito flutuando
            sombra.setColor(Qt.black)

            self.setGraphicsEffect(sombra)

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        image_path = event.mimeData().text()
        pixmap = QPixmap(image_path)
        self.setPixmap(pixmap.scaled(220, 320, Qt.KeepAspectRatio))

    # 🖱️ BOTÃO DIREITO → REMOVE
    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.clear()
            self.setText(self.title)


# 🚀 EXECUTAR
app = QApplication(sys.argv)
window = App()
window.show()
sys.exit(app.exec_())
import random
import sys
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QPoint, Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QColor, QDrag, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

PASTA_CARTAS = Path(__file__).resolve().parent / "cartas"

LARGURA_MINIATURA = 95
ALTURA_MINIATURA = 145

LARGURA_CARTA = 220
ALTURA_CARTA = 320

EXTENSOES_VALIDAS = {".png", ".jpg", ".jpeg", ".webp"}


# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def chave_ordenacao(caminho: Path):
    """
    Ordena os arquivos utilizando os números presentes no nome.

    Exemplos:
        carta2.png vem antes de carta10.png
    """
    numeros = "".join(filter(str.isdigit, caminho.stem))

    if numeros:
        return 0, int(numeros), caminho.name.lower()

    return 1, 0, caminho.name.lower()


def criar_sombra(
    blur: int = 25,
    deslocamento_y: int = 5,
    opacidade: int = 150,
) -> QGraphicsDropShadowEffect:
    sombra = QGraphicsDropShadowEffect()
    sombra.setBlurRadius(blur)
    sombra.setXOffset(0)
    sombra.setYOffset(deslocamento_y)
    sombra.setColor(QColor(0, 0, 0, opacidade))
    return sombra


# ==========================================================
# MINIATURA DA CARTA
# ==========================================================

class CartaMiniatura(QFrame):
    carta_clicada = pyqtSignal(str)

    def __init__(self, image_path: Path):
        super().__init__()

        self.image_path = image_path
        self.posicao_inicial: Optional[QPoint] = None
        self.arrastando = False

        self.configurar_interface()
        self.carregar_imagem()

    def configurar_interface(self):
        self.setObjectName("cartaMiniatura")
        self.setFixedSize(115, 185)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(
            f"{self.image_path.stem}\n"
            "Clique para adicionar.\n"
            "Arraste para uma posição."
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.imagem_label = QLabel()
        self.imagem_label.setAlignment(Qt.AlignCenter)
        self.imagem_label.setFixedSize(
            LARGURA_MINIATURA,
            ALTURA_MINIATURA,
        )
        self.imagem_label.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

        self.nome_label = QLabel(self.image_path.stem)
        self.nome_label.setAlignment(Qt.AlignCenter)
        self.nome_label.setWordWrap(True)
        self.nome_label.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

        layout.addWidget(self.imagem_label)
        layout.addWidget(self.nome_label)

    def carregar_imagem(self):
        pixmap = QPixmap(str(self.image_path))

        if pixmap.isNull():
            self.imagem_label.setText("Imagem inválida")
            return

        pixmap = pixmap.scaled(
            LARGURA_MINIATURA,
            ALTURA_MINIATURA,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.imagem_label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.posicao_inicial = event.pos()
            self.arrastando = False

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton:
            return

        if self.posicao_inicial is None:
            return

        distancia = (
            event.pos() - self.posicao_inicial
        ).manhattanLength()

        if distancia < QApplication.startDragDistance():
            return

        self.arrastando = True

        drag = QDrag(self)

        mime_data = QMimeData()
        mime_data.setText(str(self.image_path))

        drag.setMimeData(mime_data)

        pixmap = QPixmap(str(self.image_path))

        if not pixmap.isNull():
            miniatura_drag = pixmap.scaled(
                110,
                160,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            drag.setPixmap(miniatura_drag)
            drag.setHotSpot(
                QPoint(
                    miniatura_drag.width() // 2,
                    miniatura_drag.height() // 2,
                )
            )

        drag.exec_(Qt.CopyAction)

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.LeftButton
            and not self.arrastando
        ):
            self.carta_clicada.emit(str(self.image_path))

        self.posicao_inicial = None
        self.arrastando = False

        super().mouseReleaseEvent(event)


# ==========================================================
# ÁREA DE DESTINO DA CARTA
# ==========================================================

class AreaCarta(QFrame):
    carta_adicionada = pyqtSignal(object, str)
    carta_removida = pyqtSignal(object, str)

    def __init__(self, titulo: str, destaque: bool = False):
        super().__init__()

        self.titulo = titulo
        self.destaque = destaque
        self.image_path: Optional[str] = None

        self.configurar_interface()

    def configurar_interface(self):
        self.setObjectName(
            "areaFundo" if self.destaque else "areaCarta"
        )
        self.setAcceptDrops(True)
        self.setFixedSize(
            LARGURA_CARTA + 24,
            ALTURA_CARTA + 60,
        )
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.titulo_label = QLabel(self.titulo)
        self.titulo_label.setObjectName("tituloPosicao")
        self.titulo_label.setAlignment(Qt.AlignCenter)

        self.imagem_label = QLabel()
        self.imagem_label.setObjectName("imagemPosicao")
        self.imagem_label.setAlignment(Qt.AlignCenter)
        self.imagem_label.setFixedSize(
            LARGURA_CARTA,
            ALTURA_CARTA,
        )
        self.imagem_label.setText("Arraste uma carta\nou clique na biblioteca")
        self.imagem_label.setWordWrap(True)
        self.imagem_label.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

        layout.addWidget(self.titulo_label)
        layout.addWidget(
            self.imagem_label,
            alignment=Qt.AlignCenter,
        )

        self.setGraphicsEffect(
            criar_sombra(
                blur=38 if self.destaque else 22,
                deslocamento_y=8 if self.destaque else 4,
            )
        )

    def esta_vazia(self) -> bool:
        return self.image_path is None

    def definir_carta(self, image_path: str):
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            QMessageBox.warning(
                self,
                "Imagem inválida",
                f"Não foi possível abrir a imagem:\n{image_path}",
            )
            return

        caminho_anterior = self.image_path
        self.image_path = image_path

        pixmap = pixmap.scaled(
            LARGURA_CARTA,
            ALTURA_CARTA,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.imagem_label.setText("")
        self.imagem_label.setPixmap(pixmap)
        self.imagem_label.setToolTip(
            f"{Path(image_path).stem}\n"
            "Clique com o botão direito para remover."
        )

        if caminho_anterior and caminho_anterior != image_path:
            self.carta_removida.emit(self, caminho_anterior)

        self.carta_adicionada.emit(self, image_path)

    def remover_carta(self):
        if not self.image_path:
            return

        caminho_removido = self.image_path
        self.image_path = None

        self.imagem_label.clear()
        self.imagem_label.setText(
            "Arraste uma carta\nou clique na biblioteca"
        )
        self.imagem_label.setToolTip("")

        self.carta_removida.emit(self, caminho_removido)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            caminho = Path(event.mimeData().text())

            if caminho.suffix.lower() in EXTENSOES_VALIDAS:
                event.acceptProposedAction()
                return

        event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        image_path = event.mimeData().text()

        if image_path:
            self.definir_carta(image_path)
            event.acceptProposedAction()
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.remover_carta()

        super().mousePressEvent(event)


# ==========================================================
# APLICAÇÃO PRINCIPAL
# ==========================================================

class TarotApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.caminhos_cartas: list[Path] = []
        self.miniaturas: list[CartaMiniatura] = []
        self.slots: list[AreaCarta] = []

        self.configurar_janela()
        self.configurar_interface()
        self.aplicar_estilo()
        self.carregar_cartas()

    def configurar_janela(self):
        self.setWindowTitle("Tarot Studio")
        self.resize(1450, 850)
        self.setMinimumSize(1100, 700)

    def configurar_interface(self):
        widget_principal = QWidget()
        self.setCentralWidget(widget_principal)

        layout_principal = QHBoxLayout(widget_principal)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(20)

        biblioteca = self.criar_biblioteca()
        tiragem = self.criar_area_tiragem()

        layout_principal.addWidget(biblioteca)
        layout_principal.addWidget(tiragem, 1)

    # ------------------------------------------------------
    # BIBLIOTECA
    # ------------------------------------------------------

    def criar_biblioteca(self) -> QFrame:
        painel = QFrame()
        painel.setObjectName("painelBiblioteca")
        painel.setFixedWidth(410)

        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        titulo = QLabel("Biblioteca de cartas")
        titulo.setObjectName("tituloPainel")

        subtitulo = QLabel(
            "Clique ou arraste uma carta para a tiragem."
        )
        subtitulo.setObjectName("subtitulo")

        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText("Pesquisar carta...")
        self.busca_input.setClearButtonEnabled(True)
        self.busca_input.textChanged.connect(
            self.filtrar_cartas
        )

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setHorizontalSpacing(8)
        self.grid_layout.setVerticalSpacing(10)
        self.grid_layout.setAlignment(
            Qt.AlignTop | Qt.AlignHCenter
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self.grid_widget)

        self.quantidade_label = QLabel("Nenhuma carta carregada")
        self.quantidade_label.setObjectName("statusBiblioteca")
        self.quantidade_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addWidget(self.busca_input)
        layout.addWidget(scroll, 1)
        layout.addWidget(self.quantidade_label)

        return painel

    # ------------------------------------------------------
    # ÁREA DE TIRAGEM
    # ------------------------------------------------------

    def criar_area_tiragem(self) -> QFrame:
        painel = QFrame()
        painel.setObjectName("painelTiragem")

        layout = QVBoxLayout(painel)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        cabecalho_layout = QHBoxLayout()

        textos_layout = QVBoxLayout()
        textos_layout.setSpacing(3)

        titulo = QLabel("Mesa de tiragem")
        titulo.setObjectName("tituloPrincipal")

        subtitulo = QLabel(
            "Selecione três cartas e uma carta de fundo."
        )
        subtitulo.setObjectName("subtitulo")

        textos_layout.addWidget(titulo)
        textos_layout.addWidget(subtitulo)

        self.botao_aleatorio = QPushButton("Tiragem aleatória")
        self.botao_aleatorio.setObjectName("botaoPrincipal")
        self.botao_aleatorio.clicked.connect(
            self.realizar_tiragem_aleatoria
        )

        self.botao_limpar = QPushButton("Limpar")
        self.botao_limpar.setObjectName("botaoSecundario")
        self.botao_limpar.clicked.connect(
            self.limpar_tiragem
        )

        cabecalho_layout.addLayout(textos_layout)
        cabecalho_layout.addStretch()
        cabecalho_layout.addWidget(self.botao_aleatorio)
        cabecalho_layout.addWidget(self.botao_limpar)

        mesa = QWidget()
        mesa.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        mesa_layout = QGridLayout(mesa)
        mesa_layout.setContentsMargins(15, 15, 15, 15)
        mesa_layout.setHorizontalSpacing(35)
        mesa_layout.setVerticalSpacing(30)
        mesa_layout.setAlignment(Qt.AlignCenter)

        self.carta1 = AreaCarta("Carta 1")
        self.carta2 = AreaCarta("Carta 2")
        self.carta3 = AreaCarta("Carta 3")
        self.fundo = AreaCarta("Fundo da tiragem", destaque=True)

        self.slots = [
            self.carta1,
            self.carta2,
            self.carta3,
            self.fundo,
        ]

        for slot in self.slots:
            slot.carta_adicionada.connect(
                self.ao_adicionar_carta
            )
            slot.carta_removida.connect(
                self.ao_remover_carta
            )

        mesa_layout.addWidget(self.carta1, 0, 0)
        mesa_layout.addWidget(self.carta2, 0, 1)
        mesa_layout.addWidget(self.carta3, 0, 2)
        mesa_layout.addWidget(
            self.fundo,
            1,
            1,
            alignment=Qt.AlignCenter,
        )

        self.status_label = QLabel(
            "Selecione a primeira carta."
        )
        self.status_label.setObjectName("statusTiragem")
        self.status_label.setAlignment(Qt.AlignCenter)

        layout.addLayout(cabecalho_layout)
        layout.addWidget(mesa, 1)
        layout.addWidget(self.status_label)

        return painel

    # ------------------------------------------------------
    # CARREGAMENTO
    # ------------------------------------------------------

    def carregar_cartas(self):
        if not PASTA_CARTAS.exists():
            PASTA_CARTAS.mkdir(parents=True, exist_ok=True)

            QMessageBox.information(
                self,
                "Pasta criada",
                "A pasta 'cartas' foi criada.\n\n"
                "Coloque as imagens das cartas dentro dela "
                "e abra o programa novamente.",
            )

            self.quantidade_label.setText(
                "Pasta vazia: adicione as imagens"
            )
            return

        arquivos = [
            arquivo
            for arquivo in PASTA_CARTAS.iterdir()
            if arquivo.is_file()
            and arquivo.suffix.lower() in EXTENSOES_VALIDAS
        ]

        self.caminhos_cartas = sorted(
            arquivos,
            key=chave_ordenacao,
        )

        if not self.caminhos_cartas:
            self.quantidade_label.setText(
                "Nenhuma imagem encontrada"
            )
            return

        self.reconstruir_grid(self.caminhos_cartas)

    def reconstruir_grid(self, cartas: list[Path]):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)

            if item.widget():
                item.widget().deleteLater()

        self.miniaturas.clear()

        quantidade_colunas = 3

        for indice, caminho in enumerate(cartas):
            miniatura = CartaMiniatura(caminho)
            miniatura.carta_clicada.connect(
                self.colocar_carta_automaticamente
            )

            linha = indice // quantidade_colunas
            coluna = indice % quantidade_colunas

            self.grid_layout.addWidget(
                miniatura,
                linha,
                coluna,
            )

            self.miniaturas.append(miniatura)

        total = len(cartas)

        if total == 1:
            texto = "1 carta encontrada"
        else:
            texto = f"{total} cartas encontradas"

        self.quantidade_label.setText(texto)

    # ------------------------------------------------------
    # OPERAÇÕES DA TIRAGEM
    # ------------------------------------------------------

    def cartas_em_uso(
        self,
        ignorar_slot: Optional[AreaCarta] = None,
    ) -> set[str]:
        return {
            slot.image_path
            for slot in self.slots
            if slot is not ignorar_slot
            and slot.image_path is not None
        }

    def colocar_carta_automaticamente(self, image_path: str):
        if image_path in self.cartas_em_uso():
            self.status_label.setText(
                "Essa carta já está sendo utilizada."
            )
            return

        for slot in self.slots:
            if slot.esta_vazia():
                slot.definir_carta(image_path)
                return

        self.status_label.setText(
            "A tiragem já está completa. "
            "Remova uma carta para adicionar outra."
        )

    def ao_adicionar_carta(
        self,
        slot: AreaCarta,
        image_path: str,
    ):
        cartas_repetidas = [
            outro_slot
            for outro_slot in self.slots
            if outro_slot is not slot
            and outro_slot.image_path == image_path
        ]

        if cartas_repetidas:
            slot.remover_carta()

            self.status_label.setText(
                "Não é possível utilizar a mesma carta "
                "em duas posições."
            )
            return

        self.atualizar_status()

    def ao_remover_carta(
        self,
        slot: AreaCarta,
        image_path: str,
    ):
        self.atualizar_status()

    def atualizar_status(self):
        preenchidos = sum(
            not slot.esta_vazia()
            for slot in self.slots
        )

        mensagens = {
            0: "Selecione a primeira carta.",
            1: "Primeira carta selecionada.",
            2: "Duas cartas selecionadas.",
            3: "Agora selecione o fundo da tiragem.",
            4: "Tiragem completa.",
        }

        self.status_label.setText(
            mensagens.get(preenchidos, "")
        )

    def limpar_tiragem(self):
        for slot in self.slots:
            slot.remover_carta()

        self.status_label.setText(
            "Tiragem limpa. Selecione a primeira carta."
        )

    def realizar_tiragem_aleatoria(self):
        if len(self.caminhos_cartas) < len(self.slots):
            QMessageBox.warning(
                self,
                "Cartas insuficientes",
                "São necessárias pelo menos quatro cartas "
                "na pasta para realizar a tiragem aleatória.",
            )
            return

        cartas_sorteadas = random.sample(
            self.caminhos_cartas,
            len(self.slots),
        )

        self.limpar_tiragem()

        for slot, caminho in zip(
            self.slots,
            cartas_sorteadas,
        ):
            slot.definir_carta(str(caminho))

        self.status_label.setText(
            "Tiragem aleatória concluída."
        )

    # ------------------------------------------------------
    # FILTRO
    # ------------------------------------------------------

    def filtrar_cartas(self, texto: str):
        texto = texto.strip().lower()

        if not texto:
            filtradas = self.caminhos_cartas
        else:
            filtradas = [
                caminho
                for caminho in self.caminhos_cartas
                if texto in caminho.stem.lower()
            ]

        self.reconstruir_grid(filtradas)

    # ------------------------------------------------------
    # ESTILO
    # ------------------------------------------------------

    def aplicar_estilo(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #101014;
            }

            QWidget {
                color: #f4f0f7;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            QFrame#painelBiblioteca,
            QFrame#painelTiragem {
                background-color: #19191f;
                border: 1px solid #2b2932;
                border-radius: 16px;
            }

            QLabel#tituloPainel {
                color: #ffffff;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#tituloPrincipal {
                color: #ffffff;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#subtitulo {
                color: #a8a2b0;
                font-size: 13px;
            }

            QLabel#statusBiblioteca,
            QLabel#statusTiragem {
                color: #aaa3b5;
                background-color: #141419;
                border: 1px solid #2b2932;
                border-radius: 8px;
                padding: 9px;
            }

            QLineEdit {
                color: #ffffff;
                background-color: #121217;
                border: 1px solid #34313d;
                border-radius: 9px;
                padding: 10px 12px;
                selection-background-color: #805ad5;
            }

            QLineEdit:focus {
                border: 1px solid #9b6cff;
            }

            QPushButton {
                min-height: 38px;
                border-radius: 9px;
                padding: 0 18px;
                font-weight: 600;
            }

            QPushButton#botaoPrincipal {
                color: white;
                background-color: #7c4dce;
                border: 1px solid #9767e5;
            }

            QPushButton#botaoPrincipal:hover {
                background-color: #8e5ddd;
            }

            QPushButton#botaoPrincipal:pressed {
                background-color: #6940ae;
            }

            QPushButton#botaoSecundario {
                color: #eee9f4;
                background-color: #292730;
                border: 1px solid #3c3945;
            }

            QPushButton#botaoSecundario:hover {
                background-color: #35323d;
            }

            QFrame#cartaMiniatura {
                background-color: #202027;
                border: 1px solid #32303a;
                border-radius: 10px;
            }

            QFrame#cartaMiniatura:hover {
                background-color: #292732;
                border: 1px solid #9868ea;
            }

            QFrame#cartaMiniatura QLabel {
                color: #d4ceda;
                font-size: 11px;
            }

            QLabel#imagemPosicao {
                color: #77717f;
                background-color: #111116;
                border: 2px dashed #4a4652;
                border-radius: 12px;
                padding: 2px;
            }

            QLabel#tituloPosicao {
                color: #dbd5e2;
                font-size: 15px;
                font-weight: 600;
            }

            QFrame#areaCarta {
                background-color: #202027;
                border: 1px solid #35323d;
                border-radius: 14px;
            }

            QFrame#areaFundo {
                background-color: #251e2e;
                border: 1px solid #8d5bc2;
                border-radius: 14px;
            }

            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background-color: #17171c;
                width: 10px;
                margin: 0;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical {
                background-color: #45414d;
                min-height: 35px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #625b6e;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)


# ==========================================================
# EXECUÇÃO
# ==========================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Tarot Studio")

    janela = TarotApp()
    janela.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
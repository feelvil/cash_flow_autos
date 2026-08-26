"""
completer_codigos.py
====================
Búsqueda "inteligente" para el combo de códigos de cuenta.

Por defecto, un QComboBox editable filtra por prefijo: como cada item empieza
con el número (ej: "1041132 — Rentas · CÓRDOBA..."), tipear "cordoba" no
encontraría nada. Este módulo arma un QCompleter que filtra por PALABRAS
SUELTAS en cualquier orden y sin importar acentos ni mayúsculas.

Ejemplos de lo que matchea:
    "cordoba vw"  -> los códigos que tengan Córdoba Y VW (en cualquier orden)
    "cordoba"     -> todos los que tengan Córdoba
    "rentas pr"   -> los de Rentas con Plan Rombo
    "1041131"     -> sigue funcionando la búsqueda por número

Uso desde una pantalla:
    from app.ui.completer_codigos import instalar_completer_palabras
    instalar_completer_palabras(self.combo_codigo)
"""

import unicodedata

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtWidgets import QCompleter


def normalizar(texto: str) -> str:
    """
    Normaliza un texto para comparar: minúsculas y sin acentos.
    Así 'CÓRDOBA', 'córdoba' y 'cordoba' se consideran iguales.
    """
    texto = (texto or "").lower()
    # NFD separa la letra de su tilde; luego descartamos las marcas (categoría Mn).
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


class _FiltroPorPalabras(QSortFilterProxyModel):
    """
    Modelo-proxy que deja pasar una fila solo si su texto contiene TODAS las
    palabras tipeadas (en cualquier orden, sin acentos ni mayúsculas).
    
    El QCompleter usa este proxy para decidir qué sugerencias mostrar.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._palabras = []  # lista de palabras normalizadas a buscar
    
    def set_patron(self, texto: str):
        """Guarda las palabras a buscar y refresca el filtrado."""
        self._palabras = normalizar(texto).split()
        self.invalidateFilter()  # avisa a Qt que recalcule qué filas pasan
    
    def filterAcceptsRow(self, source_row, source_parent):
        # Sin palabras (campo vacío) -> mostrar todo.
        if not self._palabras:
            return True
        
        # Texto de la fila (la etiqueta del item del combo).
        indice = self.sourceModel().index(source_row, 0, source_parent)
        etiqueta = normalizar(self.sourceModel().data(indice))
        
        # Pasa solo si TODAS las palabras están en la etiqueta.
        return all(palabra in etiqueta for palabra in self._palabras)


def instalar_completer_palabras(combo) -> QCompleter:
    """
    Instala en un QComboBox editable un completer con búsqueda por palabras.
    
    Devuelve el QCompleter (por si la pantalla lo necesita), pero normalmente
    no hace falta guardarlo.
    
    Importante: hay que llamar a esto DESPUÉS de haber llenado el combo con los
    items, porque el completer toma el modelo del combo en ese momento.
    """
    # Proxy que filtra por palabras, apoyado en el modelo del propio combo.
    proxy = _FiltroPorPalabras(combo)
    proxy.setSourceModel(combo.model())
    
    completer = QCompleter(proxy, combo)
    completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
    completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    # El texto de cada sugerencia está en la columna 0.
    completer.setCompletionColumn(0)
    
    combo.setCompleter(completer)
    
    # Cada vez que el usuario tipea, actualizamos el patrón del proxy y
    # reabrimos el popup con las coincidencias.
    def _al_editar(texto):
        proxy.set_patron(texto)
        completer.complete()  # muestra el popup filtrado
    
    combo.lineEdit().textEdited.connect(_al_editar)
    
    return completer

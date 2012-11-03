################################################################################
### This is an improved version of the standard Anki REPL
### You might want to customize it to your liking
################################################################################
FONT = "Courier"
FONT_SIZE = 10
TAB_WIDTH = 32 # Must be adjusted depending on the font so that: Tab = 4 spaces;
###############################################################################

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

#############################################################################
### Syntax Highlighting for code
########
### Code copied from http://diotavelli.net/PyQtWiki/Python%20syntax%20highlighting
### with slight changes to make up for the fact that anki uses
###  > sip.api('QString', 2)
### basically, I've had to change str.length to len(str)
#############################################################################
import sys

from PyQt4.QtCore import QRegExp
from PyQt4.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter

def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('darkOrange', 'bold'),
    'operator': format('black'),
    'brace': format('darkBlue'),
    'defclass': format('darkGreen', 'bold'),
    'string': format('magenta'),
    'string2': format('darkMagenta'),
    'comment': format('gray', 'italic'),
    'self': format('brown', 'italic'),
    'numbers': format('red'),
}


class PythonHighlighter (QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
            for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
            for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
            for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
            for (pat, index, fmt) in rules]


    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)


    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False
        
class HighlightingRule():
  def __init__( self, pattern, format ):
    self.pattern = pattern
    self.format = format

##### end of syntax highlighting part #######################################
#############################################################################
from aqt.forms.debug import Ui_Dialog
from anki.hooks import wrap

def mySetupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(643, 580)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.text = QtGui.QPlainTextEdit(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(8)
        sizePolicy.setHeightForWidth(self.text.sizePolicy().hasHeightForWidth())
        self.text.setSizePolicy(sizePolicy)
        #  Make 'text' bigger than 'log', because it is really frustrating
        # to work in such a small text area for anything but the
        # most trivial code snippets
        self.text.setMaximumSize(QtCore.QSize(16777215, 16777215))
        text_font = QtGui.QFont()
        text_font.setPointSize(FONT_SIZE)
        text_font.setFamily(_fromUtf8(FONT))
        self.text.setFont(text_font)
        self.text.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
        self.text.setTabStopWidth(TAB_WIDTH) # Tab = 4 spaces
        self.text.setObjectName(_fromUtf8("text"))
        # Syntax highlighting for 'text':
        text_highlight = PythonHighlighter(self.text.document())
        self.verticalLayout.addWidget(self.text)
        
        self.log = QtGui.QPlainTextEdit(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.log.sizePolicy().hasHeightForWidth())
        self.log.setSizePolicy(sizePolicy)
        self.log.setMaximumSize(QtCore.QSize(16777215, 500))
        log_font = QtGui.QFont()
        log_font.setFamily(_fromUtf8(FONT))
        self.log.setFont(log_font)
        self.log.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.log.setReadOnly(True)
        self.log.setObjectName(_fromUtf8("log"))
        # Syntax highlighting for 'log':
        log_highlight = PythonHighlighter(self.log.document())
        self.verticalLayout.addWidget(self.log)
        
        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
    
Ui_Dialog.setupUi = mySetupUi
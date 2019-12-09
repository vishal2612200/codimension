# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2018  Sergey Satskiy <sergey.satskiy@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Virtual canvas items to handle groups (opened/collapsed)"""


from html import escape
from ui.qt import (Qt, QPen, QBrush, QGraphicsRectItem, QGraphicsItem, QFrame,
                   QLabel, QVBoxLayout, QPalette, QApplication)
from utils.globals import GlobalData
from .cellelement import CellElement
from .auxitems import Connector
from .colormixin import ColorMixin


class HGroupSpacerCell(CellElement):

    """Represents a horizontal spacer cell used to shift items due to groups"""

    def __init__(self, ref, canvas, x, y):
        CellElement.__init__(self, ref, canvas, x, y)
        self.kind = CellElement.H_GROUP_SPACER

        # Number of spacers to be inserted
        self.count = 0

    def render(self):
        """Renders the cell"""
        self.width = self.count * 2 * self.canvas.settings.openGroupHSpacer
        self.height = 0
        self.minWidth = self.width
        self.minHeight = self.height
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        # There is no need to draw anything. The cell just reserves some
        # horizontal space for better appearance
        self.baseX = baseX
        self.baseY = baseY


class GroupItemBase():

    """Common functionality for the group items"""

    def __init__(self, groupBeginCMLRef):
        self.nestedRefs = []

        self.groupBeginCMLRef = groupBeginCMLRef
        self.groupEndCMLRef = None

        # True if the previous item is terminal, i.e no connector needed
        self.isTerminal = False

    def getGroupId(self):
        """Provides the group ID"""
        return self.groupBeginCMLRef.id

    def _getText(self):
        """Provides the box text"""
        if self._text is None:
            self._text = self.groupBeginCMLRef.getTitle()
            if self.canvas.settings.noContent:
                if self._text:
                    self.setToolTip('<pre>' + escape(self._text) + '</pre>')
                self._text = ''
        return self._text

    def getTitle(self):
        """Convenience for the UI"""
        return self.groupBeginCMLRef.getTitle()

    def getLineRange(self):
        """Provides the line range"""
        return [self.groupBeginCMLRef.ref.beginLine,
                self.groupEndCMLRef.ref.endLine]

    def getAbsPosRange(self):
        """Provides the absolute position range"""
        return [self.groupBeginCMLRef.ref.begin,
                self.groupEndCMLRef.ref.end]

    def getSelectTooltip(self):
        """Provides the tooltip"""
        lineRange = self.getLineRange()
        return 'Group at lines ' + \
               str(lineRange[0]) + "-" + str(lineRange[1])


class EmptyGroup(GroupItemBase, CellElement, ColorMixin, QGraphicsRectItem):

    """Represents an empty group"""

    N_BACK_RECT = 2

    def __init__(self, ref, groupBeginCMLRef, canvas, x, y):
        GroupItemBase.__init__(self, groupBeginCMLRef)
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, None, canvas.settings.emptyGroupBGColor,
                            canvas.settings.emptyGroupFGColor,
                            canvas.settings.emptyGroupBorderColor,
                            colorSpec=groupBeginCMLRef)
        QGraphicsRectItem.__init__(self, canvas.scopeRectangle)
        self.kind = CellElement.EMPTY_GROUP

        self.__textRect = None
        self.connector = None

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self._getText())

        vPadding = 2 * (settings.vCellPadding + settings.vTextPadding) + \
                   self.N_BACK_RECT * settings.emptyGroupYShift
        self.minHeight = self.__textRect.height() + vPadding
        hPadding = 2 * (settings.hCellPadding + settings.hTextPadding) + \
                   self.N_BACK_RECT * settings.emptyGroupXShift
        self.minWidth = max(self.__textRect.width() + hPadding,
                            settings.minWidth)
        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        # Add the connector as a separate scene item to make the selection
        # working properly
        settings = self.canvas.settings
        self.connector = Connector(self.canvas, baseX + settings.mainLine, baseY,
                                   baseX + settings.mainLine,
                                   baseY + self.height)
        scene.addItem(self.connector)

        # Setting the rectangle is important for the selection and for
        # redrawing. Thus the selection pen with must be considered too.
        penWidth = settings.selectPenWidth - 1
        self.setRect(baseX + settings.hCellPadding - penWidth,
                     baseY + settings.vCellPadding - penWidth,
                     self.minWidth - 2 * settings.hCellPadding + 2 * penWidth,
                     self.minHeight - 2 * settings.vCellPadding + 2 * penWidth)
        scene.addItem(self)

    def paint(self, painter, option, widget):
        """Draws the collapsed group"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        # Outer rectangle
        rectWidth = self.minWidth - 2 * settings.hCellPadding - \
                    self.N_BACK_RECT * settings.emptyGroupXShift
        rectHeight = self.minHeight - 2 * settings.vCellPadding - \
                     self.N_BACK_RECT * settings.emptyGroupYShift

        if self.isSelected():
            pen = QPen(settings.selectColor)
            pen.setWidth(settings.selectPenWidth)
            pen.setJoinStyle(Qt.RoundJoin)
        else:
            pen = QPen(self.borderColor)
            pen.setStyle(Qt.DotLine)
            pen.setWidth(1)
        painter.setPen(pen)
        brush = QBrush(self.bgColor)
        painter.setBrush(brush)

        for rectNum in range(self.N_BACK_RECT, -1, -1):
            xPos = self.baseX + settings.hCellPadding + \
                   rectNum * settings.emptyGroupXShift
            yPos = self.baseY + settings.vCellPadding + \
                   (self.N_BACK_RECT - rectNum) * settings.emptyGroupYShift
            painter.drawRect(xPos, yPos, rectWidth, rectHeight)

        # Draw the text in the rectangle
        pen = QPen(self.fgColor)
        painter.setFont(settings.monoFont)
        painter.setPen(pen)

        textWidth = self.__textRect.width() + 2 * settings.hTextPadding
        textShift = (rectWidth - textWidth) / 2
        painter.drawText(
            self.baseX + settings.hCellPadding +
            settings.hTextPadding +
            textShift,
            self.baseY + settings.vCellPadding + settings.vTextPadding +
            self.N_BACK_RECT * settings.emptyGroupYShift,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self._getText())


class OpenedGroupBegin(GroupItemBase, CellElement,
                       ColorMixin, QGraphicsRectItem):

    """Represents beginning af a group which can be collapsed"""

    def __init__(self, ref, groupBeginCMLRef, canvas, x, y):
        GroupItemBase.__init__(self, groupBeginCMLRef)
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, None, canvas.settings.openGroupBGColor,
                            canvas.settings.openGroupFGColor,
                            canvas.settings.openGroupBorderColor,
                            colorSpec=groupBeginCMLRef)
        QGraphicsRectItem.__init__(self, canvas.scopeRectangle)
        self.kind = CellElement.OPENED_GROUP_BEGIN
        self.connector = None
        self.topLeftControl = None
        self.highlight = False

        # These two items are filled when rendering is finished for all the
        # items in the group
        self.groupWidth = None
        self.groupHeight = None

        self.groupEndRow = None
        self.groupEndColumn = None

        self.selfAndDeeperNestLevel = None
        self.selfMaxNestLevel = None    # Used in vcanvas.py

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def setHighlight(self, newValue):
        """Changes the highlight status of the group"""
        if self.highlight != newValue:
            self.highlight = newValue
            if not self.isSelected():
                self.update()

    def render(self):
        """Renders the cell"""
        self.topLeftControl = GroupCornerControl(self)
        self.width = self.canvas.settings.openGroupVSpacer * 2
        self.height = self.canvas.settings.openGroupVSpacer * 2
        self.minWidth = self.width
        self.minHeight = self.height
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        settings = self.canvas.settings

        # Setting the rectangle is important for the selection and for
        # redrawing. Thus the selection pen with must be considered too.
        penWidth = settings.selectPenWidth - 1

        groupWidth = self.groupWidth + 2 * settings.openGroupHSpacer

        self.setRect(baseX - penWidth + settings.openGroupHSpacer,
                     baseY - penWidth + settings.openGroupVSpacer,
                     groupWidth + 2 * penWidth,
                     self.groupHeight +
                     2 * (penWidth + settings.openGroupVSpacer))
        scene.addItem(self)

        # Add the connector as a separate scene item to make the selection
        # working properly. The connector must be added after a group,
        # otherwise a half of it is hidden by the group.
        if not self.isTerminal:
            xPos = baseX + settings.mainLine
            xPos += self.selfAndDeeperNestLevel * (2 * settings.openGroupHSpacer)
            self.connector = Connector(self.canvas,
                                       xPos,
                                       baseY,
                                       xPos,
                                       baseY + settings.openGroupVSpacer * 2)
            scene.addItem(self.connector)

        # Top left corner control
        self.topLeftControl.moveTo(baseX, baseY)
        scene.addItem(self.topLeftControl)

    def paint(self, painter, option, widget):
        """Draws the collapsed group"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        # Group rectangle
        if self.isSelected():
            selectPen = QPen(settings.selectColor)
            selectPen.setWidth(settings.selectPenWidth)
            selectPen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(selectPen)
        else:
            pen = QPen(self.borderColor)
            if self.highlight:
                pen.setStyle(Qt.SolidLine)
            else:
                pen.setStyle(Qt.DotLine)
            pen.setWidth(1)
            painter.setPen(pen)
        brush = QBrush(self.bgColor)
        painter.setBrush(brush)

        fullWidth = self.groupWidth + 2 * settings.openGroupHSpacer
        fullHeight = self.groupHeight + 2 * settings.openGroupVSpacer
        painter.drawRoundedRect(self.baseX + settings.openGroupHSpacer,
                                self.baseY + settings.openGroupVSpacer,
                                fullWidth, fullHeight,
                                settings.openGroupVSpacer,
                                settings.openGroupVSpacer)


class OpenedGroupEnd(GroupItemBase, CellElement):

    """Represents the end af a group which can be collapsed"""

    def __init__(self, ref, groupBeginCMLRef, canvas, x, y):
        GroupItemBase.__init__(self, groupBeginCMLRef)
        CellElement.__init__(self, ref, canvas, x, y)
        self.kind = CellElement.OPENED_GROUP_END

        self.groupBeginRow = None
        self.groupBeginColumn = None

        self.selfAndDeeperNestLevel = None

    def render(self):
        """Renders the cell"""
        self.width = 0
        self.height = self.canvas.settings.openGroupVSpacer * 2
        self.minWidth = self.width
        self.minHeight = self.height
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        if self.isTerminal:
            return

        # Add the connector as a separate scene item to make the selection
        # working properly
        settings = self.canvas.settings
        xPos = baseX + settings.mainLine
        xPos += self.selfAndDeeperNestLevel * (2 * settings.openGroupHSpacer)
        self.connector = Connector(self.canvas,
                                   xPos,
                                   baseY,
                                   xPos,
                                   baseY + settings.openGroupVSpacer * 2)
        scene.addItem(self.connector)



class CollapsedGroup(GroupItemBase, CellElement,
                     ColorMixin, QGraphicsRectItem):

    """Represents a collapsed group"""

    N_BACK_RECT = 2

    def __init__(self, ref, groupBeginCMLRef, canvas, x, y):
        GroupItemBase.__init__(self, groupBeginCMLRef)
        CellElement.__init__(self, ref, canvas, x, y)
        ColorMixin.__init__(self, None, canvas.settings.collapsedGroupBGColor,
                            canvas.settings.collapsedGroupFGColor,
                            canvas.settings.collapsedGroupBorderColor,
                            colorSpec=groupBeginCMLRef)
        QGraphicsRectItem.__init__(self, canvas.scopeRectangle)
        self.kind = CellElement.COLLAPSED_GROUP
        self.__textRect = None
        self.connector = None

        # To make double click delivered
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

    def render(self):
        """Renders the cell"""
        settings = self.canvas.settings
        self.__textRect = self.getBoundingRect(self._getText())

        vPadding = 2 * (settings.vCellPadding + settings.vTextPadding) + \
                   self.N_BACK_RECT * settings.collapsedGroupYShift
        self.minHeight = self.__textRect.height() + vPadding
        hPadding = 2 * (settings.hCellPadding + settings.hTextPadding) + \
                   self.N_BACK_RECT * settings.collapsedGroupXShift
        self.minWidth = max(self.__textRect.width() + hPadding,
                            settings.minWidth)
        self.height = self.minHeight
        self.width = self.minWidth
        return (self.width, self.height)

    def draw(self, scene, baseX, baseY):
        """Draws the cell"""
        self.baseX = baseX
        self.baseY = baseY

        # Add the connector as a separate scene item to make the selection
        # working properly
        settings = self.canvas.settings
        self.connector = Connector(self.canvas, baseX + settings.mainLine, baseY,
                                   baseX + settings.mainLine,
                                   baseY + self.height)
        scene.addItem(self.connector)

        # Setting the rectangle is important for the selection and for
        # redrawing. Thus the selection pen with must be considered too.
        penWidth = settings.selectPenWidth - 1
        self.setRect(baseX + settings.hCellPadding - penWidth,
                     baseY + settings.vCellPadding - penWidth,
                     self.minWidth - 2 * settings.hCellPadding + 2 * penWidth,
                     self.minHeight - 2 * settings.vCellPadding + 2 * penWidth)
        scene.addItem(self)

    def paint(self, painter, option, widget):
        """Draws the collapsed group"""
        del option      # unused argument
        del widget      # unused argument

        settings = self.canvas.settings

        # Outer rectangle
        rectWidth = self.minWidth - 2 * settings.hCellPadding - \
                    self.N_BACK_RECT * settings.collapsedGroupXShift
        rectHeight = self.minHeight - 2 * settings.vCellPadding - \
                     self.N_BACK_RECT * settings.collapsedGroupYShift

        if self.isSelected():
            pen = QPen(settings.selectColor)
            pen.setWidth(settings.selectPenWidth)
            pen.setJoinStyle(Qt.RoundJoin)
        else:
            pen = QPen(self.borderColor)
        painter.setPen(pen)
        brush = QBrush(self.bgColor)
        painter.setBrush(brush)

        for rectNum in range(self.N_BACK_RECT, -1, -1):
            xPos = self.baseX + settings.hCellPadding + \
                   rectNum * settings.collapsedGroupXShift
            yPos = self.baseY + settings.vCellPadding + \
                   (self.N_BACK_RECT - rectNum) * settings.collapsedGroupYShift
            painter.drawRect(xPos, yPos, rectWidth, rectHeight)

        # Draw the text in the rectangle
        pen = QPen(self.fgColor)
        painter.setFont(settings.monoFont)
        painter.setPen(pen)

        textWidth = self.__textRect.width() + 2 * settings.hTextPadding
        textShift = (rectWidth - textWidth) / 2
        painter.drawText(
            self.baseX + settings.hCellPadding +
            settings.hTextPadding +
            textShift,
            self.baseY + settings.vCellPadding + settings.vTextPadding +
            self.N_BACK_RECT * settings.collapsedGroupYShift,
            self.__textRect.width(), self.__textRect.height(),
            Qt.AlignLeft, self._getText())



class GroupCornerControl(QGraphicsRectItem):

    """Expanded group top left corner control"""

    def __init__(self, ref):
        QGraphicsRectItem.__init__(self)
        self.ref = ref

        settings = self.ref.canvas.settings
        self.__width = settings.openGroupHSpacer * 2 - 1
        self.__height = settings.openGroupVSpacer * 2 - 1

        self.setAcceptHoverEvents(True)

    def moveTo(self, xPos, yPos):
        """Moves to the specified position"""
        settings = self.ref.canvas.settings

        # This is a mistery. I do not understand why I need to divide by 2.0
        # however this works. I tried various combinations of initialization,
        # setting the position and mapping. Nothing works but ../2.0. Sick!
        self.setPos((float(xPos) + settings.openGroupHSpacer - 1) / 2.0,
                    (float(yPos) + settings.openGroupVSpacer - 1) / 2.0)
        self.setRect(self.x(), self.y(),
                     self.__width, self.__height)

    def paint(self, painter, option, widget):
        """Paints the control"""
        del option
        del widget

        settings = self.ref.canvas.settings

        pen = QPen(settings.openGroupControlBorderColor)
        pen.setStyle(Qt.SolidLine)
        pen.setWidth(1)
        painter.setPen(pen)

        brush = QBrush(settings.openGroupControlBGColor)
        painter.setBrush(brush)

        painter.drawRoundedRect(self.x(), self.y(),
                                self.__width, self.__height,
                                1, 1)

    def hoverEnterEvent(self, event):
        """Handles the mouse in event"""
        del event
        self.ref.setHighlight(True)
        if self.ref.getTitle():
            groupTitlePopup.setTitleForGroup(self.ref)
            groupTitlePopup.show(self)

    def hoverLeaveEvent(self, event):
        """Handles the mouse out event"""
        del event
        self.ref.setHighlight(False)
        groupTitlePopup.hide()

    def isProxyItem(self):
        """True if it is a proxy item"""
        return True

    def getProxiedItem(self):
        """Provides the real item for a proxy one"""
        return self.ref

    def isComment(self):
        """True if it is a comment"""
        return False

    def isCMLDoc(self):
        """True if it is a CML doc item"""
        return False

    def scopedItem(self):
        """True if it is a scoped item"""
        return False



class GroupTitlePopup(QFrame):

    """Frameless panel to show the group title"""

    def __init__(self, parent):
        QFrame.__init__(self, parent)

        self.setWindowFlags(Qt.SplashScreen |
                            Qt.WindowStaysOnTopHint |
                            Qt.X11BypassWindowManagerHint)

        self.setFrameShape(QFrame.StyledPanel)
        self.setLineWidth(1)

        self.__titleLabel = None
        self.__createLayout()

    def __createLayout(self):
        """Creates the widget layout"""
        verticalLayout = QVBoxLayout(self)
        verticalLayout.setContentsMargins(0, 0, 0, 0)

        self.__titleLabel = QLabel()
        self.__titleLabel.setAutoFillBackground(True)
        self.__titleLabel.setFrameShape(QFrame.StyledPanel)
        self.__titleLabel.setStyleSheet('padding: 2px')
        verticalLayout.addWidget(self.__titleLabel)

    def setTitleForGroup(self, group):
        """Sets the title of the group"""
        self.__titleLabel.setFont(group.canvas.settings.monoFont)
        self.__titleLabel.setText(group.getTitle())

    def resize(self, controlItem):
        """Moves the popup to the proper position"""
        # calculate the positions above the group
        # Taken from here:
        # https://stackoverflow.com/questions/9871749/find-screen-position-of-a-qgraphicsitem
        scene = controlItem.ref.scene()
        view = scene.views()[0]
        sceneP = controlItem.mapToScene(controlItem.boundingRect().topLeft())
        viewP = view.mapFromScene(sceneP)
        pos = view.viewport().mapToGlobal(viewP)

        self.move(pos.x(), pos.y() - self.height() - 2)
        QApplication.processEvents()

    def show(self, controlItem):
        """Shows the title above the group control"""
        # Use the palette from the group
        bgColor, fgColor, _ = controlItem.ref.getColors()
        palette = self.__titleLabel.palette()
        palette.setColor(QPalette.Background, bgColor)
        palette.setColor(QPalette.Foreground, fgColor)
        self.__titleLabel.setPalette(palette)

        # That's a trick: resizing works correctly only if the item is shown
        # So move it outside of the screen, show it so it is invisible and then
        # resize and move to the proper position
        screenHeight = GlobalData().screenHeight
        self.move(0, screenHeight + 128)
        QFrame.show(self)
        QApplication.processEvents()
        self.resize(controlItem)

# One instance use for all
groupTitlePopup = GroupTitlePopup(None)


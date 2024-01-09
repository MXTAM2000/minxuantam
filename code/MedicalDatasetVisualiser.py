import sys
from vtk import *
import vtk
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QAction, QMdiSubWindow,\
    QToolBar, QLabel, QPushButton, QDockWidget, QGridLayout, QVBoxLayout, QLineEdit,\
    QTextEdit, QWidget, QToolBox, QCheckBox, QFrame, QFileDialog, QDialog, QMenu
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import Qt
from PyQt5.QtCore import QTimer
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import cv2
from vtkmodules.util import numpy_support
import subprocess
import matplotlib as plt
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pydicom
from matplotlib.widgets import Slider
import os
import re
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMdiSubWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QCheckBox
import os
import pydicom
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.widgets import Slider
from matplotlib import cm
import cv2
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.widgets import Button
from matplotlib.patches import Circle
from scipy.interpolate import interp1d
from matplotlib.path import Path
import matplotlib.patches as patches

class StatusMessage:
    @staticmethod
    def format(slice: int, max_slice: int):
        return f'Slice Number {slice + 1}/{max_slice + 1}'

class MatplotlibWidget(QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget, self).__init__(parent)
        self.figure, self.ax = plt.subplots()
        self.slider = None
        self.edge_plot = None
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
      
        self.draw_mode = False  # Flag to indicate whether drawing is enabled or not
        self.circle_mode = False
        self.delete_mode = False  # Flag to indicate whether deletion mode is enabled or not
        self.paint_mode = False

        self.checkbox_draw = QCheckBox('Draw Line', self)
        self.checkbox_draw.stateChanged.connect(self.toggle_drawing)
        
        self.checkbox_circle = QCheckBox('Draw Circle', self)
        self.checkbox_circle.stateChanged.connect(self.toggle_circle)

        self.checkbox_delete = QCheckBox('Delete', self)
        self.checkbox_delete.stateChanged.connect(self.toggle_deletion)

        self.checkbox_paint = QCheckBox('Paint Mode', self)
        self.checkbox_paint.stateChanged.connect(self.toggle_painting)

        self.clear_button = QPushButton('Clear', self)
        self.clear_button.clicked.connect(self.clear_canvas)
    
        # Add the checkboxes to the layout
        layout.addWidget(self.checkbox_paint)
        layout.addWidget(self.checkbox_draw)
        layout.addWidget(self.checkbox_circle)
        layout.addWidget(self.checkbox_delete)
        layout.addWidget(self.clear_button)      

        # Variable to store mouse coordinates for drawing lines
        self.x_start, self.y_start = None, None
        self.line = None  # Store the Line2D object for updating
        self.lines = []  # Store all drawn lines
        self.shape = None  # Store the shape object for updating
        self.shapes = []  # Store all drawn shapes (lines or circles)

        # Connect mouse press, release, and motion events
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('button_release_event', self.on_release)

    def toggle_painting(self, state):
        if state == 2:  # Checkbox is checked
            self.paint_mode = True
            self.delete_mode = False
            self.draw_mode = False
            self.circle_mode = False
            self.checkbox_delete.setChecked(False)
            self.checkbox_draw.setChecked(False)
            self.checkbox_circle.setChecked(False)
        else:
            self.paint_mode = False

    def toggle_drawing(self, state):
        if state == 2:  # Checkbox is checked
            self.draw_mode = True
            self.paint_mode = False
            self.delete_mode = False
            self.circle_mode = False
            self.checkbox_delete.setChecked(False)
            self.checkbox_circle.setChecked(False)
            self.checkbox_paint.setChecked(False)
        else:
            self.draw_mode = False

    def toggle_deletion(self, state):
        if state == 2:  # Checkbox is checked
            self.delete_mode = True
            self.paint_mode = False
            self.draw_mode = False
            self.circle_mode = False
            self.checkbox_draw.setChecked(False)
            self.checkbox_circle.setChecked(False)
            self.checkbox_paint.setChecked(False)
        else:
            self.delete_mode = False
    
    def toggle_circle(self, state):
        if state == 2:  # Checkbox is checked
            self.circle_mode = True
            self.paint_mode = False
            self.draw_mode = False
            self.delete_mode = False
            self.checkbox_draw.setChecked(False)
            self.checkbox_delete.setChecked(False)
            self.checkbox_paint.setChecked(False)
        else:
            self.circle_mode = False

    def on_press(self, event):
        if self.draw_mode and event.button == 1:  # Check if drawing mode is enabled and left mouse button is pressed
            self.x_start, self.y_start = event.xdata, event.ydata
            self.line = Line2D([self.x_start, self.x_start], [self.y_start, self.y_start],
                               transform=self.ax.transData, color='red')
            self.ax.add_line(self.line)
            self.lines.append(self.line)
            self.canvas.draw()

        elif self.delete_mode and event.button == 1:
            # Check for lines to delete
            for line in self.lines:
                contains, _ = line.contains(event)
                if contains:
                    self.ax.lines.remove(line)
                    self.lines.remove(line)
                    self.canvas.draw()

            # Check for shapes (circles) to delete
            for shape in self.shapes:
                contains = shape.contains(event)
                if contains:
                    self.ax.patches.remove(shape)
                    self.shapes.remove(shape)
                    self.canvas.draw()

        elif self.circle_mode and event.button == 1:  # Check if circle drawing mode is enabled and left mouse button is pressed
            self.x_start, self.y_start = event.xdata, event.ydata
            self.shape = Circle((self.x_start, self.y_start), radius=0, fill=False, color='blue')
            self.ax.add_patch(self.shape)
            self.shapes.append(self.shape)
            self.canvas.draw()    

        elif self.paint_mode and event.button == 1:
            x, y = event.xdata, event.ydata
            self.x_start, self.y_start = x, y
            self.line = [] 

    def on_motion(self, event):
        if self.draw_mode and event.button == 1 and self.x_start is not None and self.y_start is not None:
            if self.line:
                x_end, y_end = event.xdata, event.ydata
                self.line.set_xdata([self.x_start, x_end])
                self.line.set_ydata([self.y_start, y_end])
                self.canvas.draw()
        
        elif self.circle_mode and event.button == 1 and self.x_start is not None and self.y_start is not None:
            if self.shape:
                x_end, y_end = event.xdata, event.ydata
                radius = ((x_end - self.x_start) ** 2 + (y_end - self.y_start) ** 2) ** 0.5
                self.shape.set_radius(radius)
                self.canvas.draw()
        
        if self.paint_mode and event.button == 1 and event.xdata is not None and event.ydata is not None:
            x, y = event.xdata, event.ydata
            if self.x_start is not None and self.y_start is not None:
                # Create a path to connect the points for smooth drawing
                verts = [
                    (self.x_start, self.y_start),
                    (x, y),
                ]
                codes = [Path.MOVETO, Path.LINETO]

                path = Path(verts, codes)
                patch = patches.PathPatch(path, transform=self.ax.transData, color='green', lw=2)
                self.ax.add_patch(patch)
                self.canvas.draw()

                # Update starting point for next segment
                self.x_start, self.y_start = x, y
            else:
                self.x_start, self.y_start = x, y

    def on_release(self, event):
        if self.draw_mode and event.button == 1 and self.x_start is not None and self.y_start is not None:
            self.x_start, self.y_start = None, None
            self.line = None
            self.shape = None
        
        elif self.paint_mode and event.button == 1:
            # Keep the coordinates if still in painting mode
            self.x_start, self.y_start = event.xdata, event.ydata
    
    def clear_canvas(self):
        # Clear all drawn lines, shapes, or paintings
        for line in self.lines:
            line.remove()
        self.lines = []

        for shape in self.shapes:
            shape.remove()
        self.shapes = []

        for patch in self.ax.patches:
            patch.remove()

        self.canvas.draw()
            
# Define own interaction style
class MyVtkInteractorStyleImage(vtkInteractorStyleImage):
    def __init__(self, parent=None):
        super().__init__()
        self.AddObserver('KeyPressEvent', self.KeyPressEvent)
        self.AddObserver('MouseWheelForwardEvent', self.MouseWheelBackwardEvent)
        self.AddObserver('MouseWheelBackwardEvent', self.MouseWheelForwardEvent)
        self.image_viewer = None
        self.status_mapper = None
        self.slice = 0
        self.min_slice = 0
        self.max_slice = 0

    def set_image_viewer(self, image_viewer):
        self.image_viewer = image_viewer
        self.image_viewer.GetRenderer().SetViewport(0, 0, 1, 1)  # Full viewport
        self.min_slice = image_viewer.GetSliceMin()
        self.max_slice = image_viewer.GetSliceMax()
        self.slice = self.min_slice
        print(f'Slicer: Min = {self.min_slice}, Max= {self.max_slice}')

    def set_status_mapper(self, status_mapper):
        self.status_mapper = status_mapper

    def move_slice_forward(self):
        if self.slice < self.max_slice:
            self.slice += 1
            print(f'MoveSliceForward::Slice = {self.slice}')
            self.image_viewer.SetSlice(self.slice)
            msg = StatusMessage.format(self.slice, self.max_slice)
            self.status_mapper.SetInput(msg)
            self.image_viewer.Render()

    def move_slice_backward(self):
        if self.slice > self.min_slice:
            self.slice -= 1
            print(f'MoveSliceBackward::Slice = {self.slice}')
            self.image_viewer.SetSlice(self.slice)
            msg = StatusMessage.format(self.slice, self.max_slice)
            self.status_mapper.SetInput(msg)
            self.image_viewer.Render()

    def KeyPressEvent(self, obj, event):
        key = self.GetInteractor().GetKeySym()
        if key == 'Up':
            print("1")
            self.move_slice_forward()
        elif key == 'Down':
            print("2")
            self.move_slice_backward()

    def MouseWheelForwardEvent(self, obj, event):
        self.move_slice_forward()
        

    def MouseWheelBackwardEvent(self, obj, event):
        self.move_slice_backward()

# Read all the DICOM files in the specified directory.
def get_program_parameters(file_path=None):
    import argparse
    app = QApplication(sys.argv)
    dirname = QFileDialog.getExistingDirectory(None, "Select DICOM Directory")
    return dirname

class AppWindow(QMainWindow):
    count = 0

    def __init__(self):
        super().__init__()
        self.initializeUI()
        self.vtkWidget = None
        self.loaded_dicom_files = []  # To store loaded DICOM file paths
        self.file_name = None
        #self.open_vtk_file()

    def initializeUI(self):
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'icon_ass2', 'dicom_icon.png')))
        self.setWindowTitle("DICOM: Medical Data Visualizer")
        self.setGeometry(100, 100, 1200, 800)  # Set initial window geometry
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        self.resize(1200, 800)
        self.menu_bar()
        self.tool_bar()
        self.docker_widget()
        self.showMaximized()

    def menu_bar(self):
        bar = self.menuBar()
        file = bar.addMenu('File')
        file_new = self.create_action('New', 'icon_ass2\\add.png', 'Ctrl+N', self.file_open_thr)
        file_slice = self.create_action('Slice', 'icon_ass2\\layer.png', 'Ctrl+S', self.open_vtk_file)
        file_plt = self.create_action('Matplotlib', 'icon_ass2\\matplotlib.png', 'Ctrl+M', self.axial_dicom)
        file_exit = self.create_action('Quit', 'icon_ass2\\exit.png', 'Ctrl+Q', self.close)
        self.add_action(file, (file_new, file_slice, file_plt, file_exit))

    def open_vtk_file(self):
        vtk_widget = None
        try:
            colors = vtkNamedColors()
            reader = vtkDICOMImageReader()
            folder = QFileDialog.getExistingDirectory(self, 'Select Folder')
            # Read DICOM files in the specified directory
            reader = vtk.vtkDICOMImageReader()
            reader.SetDirectoryName(folder)
            reader.Update()

            # Visualilze
            image_viewer = vtkImageViewer2()
            image_viewer.SetInputConnection(reader.GetOutputPort())
            # Slice status message
            slice_text_prop = vtkTextProperty()
            slice_text_prop.SetFontFamilyToCourier()
            slice_text_prop.SetFontSize(20)
            slice_text_prop.SetVerticalJustificationToBottom()
            slice_text_prop.SetJustificationToLeft()
            # Slice status message
            slice_text_mapper = vtkTextMapper()
            msg = StatusMessage.format(image_viewer.GetSliceMin(), image_viewer.GetSliceMax())
            slice_text_mapper.SetInput(msg)
            slice_text_mapper.SetTextProperty(slice_text_prop)

            slice_text_actor = vtkActor2D()
            slice_text_actor.SetMapper(slice_text_mapper)
            slice_text_actor.SetPosition(15, 10)

            # Usage hint message
            usage_text_prop = vtkTextProperty()
            usage_text_prop.SetFontFamilyToCourier()
            usage_text_prop.SetFontSize(14)
            usage_text_prop.SetVerticalJustificationToTop()
            usage_text_prop.SetJustificationToLeft()
            usage_text_mapper = vtkTextMapper()
            usage_text_mapper.SetInput(
                'Slice with mouse wheel\n  or Up/Down-Key\n- Zoom with pressed right\n '
                ' mouse button while dragging'
            )
            usage_text_mapper.SetTextProperty(usage_text_prop)

            usage_text_actor = vtkActor2D()
            usage_text_actor.SetMapper(usage_text_mapper)
            usage_text_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
            usage_text_actor.GetPositionCoordinate().SetValue(0.05, 0.95)

            my_interactor_style = MyVtkInteractorStyleImage()

            # Make imageviewer2 and sliceTextMapper visible to our interactorstyle
            # to enable slice status message updates when  scrolling through the slices.
            my_interactor_style.set_image_viewer(image_viewer)
            my_interactor_style.set_status_mapper(slice_text_mapper)

            # Add slice status message and usage hint message to the renderer.
            image_viewer.GetRenderer().AddActor2D(slice_text_actor)
            image_viewer.GetRenderer().AddActor2D(usage_text_actor)

            # Create a QVTKRenderWindowInteractor
            vtk_widget = QVTKRenderWindowInteractor(parent=self)
            image_viewer.GetRenderer().SetBackground(colors.GetColor3d('SlateGray'))
            image_viewer.SetRenderWindow(vtk_widget.GetRenderWindow())
            image_viewer.SetupInteractor(vtk_widget)
            #image_viewer.GetRenderer().SetViewport(0, 0, 1, 1)  # Full viewport
            vtk_widget.SetInteractorStyle(my_interactor_style)
            vtk_widget.Render()
            #vtk_widget.GetRenderWindow().AddRenderer(image_viewer.GetRenderer())
            #vtk_widget.Render()
        
            
            # Set the interactor style
            my_interactor_style = MyVtkInteractorStyleImage()
            my_interactor_style.set_image_viewer(image_viewer)
            my_interactor_style.set_status_mapper(slice_text_mapper)
            vtk_widget.GetRenderWindow().GetInteractor().SetInteractorStyle(my_interactor_style)


            # Create a QMdiSubWindow and set vtk_widget as its central widget
            sub_window = QMdiSubWindow(self.mdi)
            sub_window.setWidget(vtk_widget)
            sub_window.setWindowTitle("VTK Visualization")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

            vtk_widget.GetRenderWindow().GetInteractor().Disable()
            
            # Connect VTK interactor events to Qt's event loop
            def qt_update():
                if not vtk_widget.isHidden():
                    vtk_widget.GetRenderWindow().Render()
                    QTimer.singleShot(30, qt_update)

            QTimer.singleShot(30, qt_update)
 
        except FileNotFoundError:
            print("External file not found or unable to execute.")

    def tool_bar(self):

        navToolBar = self.addToolBar("Navigation")
        homeAction = self.create_action('Clear', 'icon_ass2\\home.png', 'Ctrl+H', self.close_all_subwindows)
        newAction = self.create_action('Single Mode', 'icon_ass2\\add.png', 'Ctrl+N', self.file_open_thr)
        sliceAction = self.create_action('Slice Mode', 'icon_ass2\\layer.png', 'Ctrl+S', self.open_vtk_file)
        #toolAction = self.create_action('Show tool widget', 'D:\\DataSetTutorialVTK\\icon_ass2\\tool_icon.png', 'F2', self.docker_widget)
        pltAction = self.create_action('Matplotlib Mode', 'icon_ass2\\matplotlib.png', 'F2', self.axial_dicom)

        self.add_action(navToolBar, (homeAction, newAction, sliceAction, pltAction))
        navToolBar.setFloatable(False)

    def close_all_subwindows(self):
        for sub_window in self.mdi.subWindowList():
            sub_window.close()

    def create_action(self, text, icon=None, shortcut=None, implement=None, signal='triggered'):
        action = QtWidgets.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon(icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if implement is not None:
            getattr(action, signal).connect(implement)
        return action

    def add_action(self, dest, actions):
        for action in actions:
            if action is None:
                dest.addSeperator()
            else:
                dest.addAction(action)

    def show_tiled(self):
        self.mdi.tileSubWindows()

    def file_open_thr(self):


        AppWindow.count = AppWindow.count + 1
        self.filename = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

        if self.filename:
            self.vtk(self.filename)
            self.vtkWidget = self.vtkWidget  # Update vtkWidget when DICOM file is loaded
            # Update loaded_dicom_files with the loaded DICOM files
            self.loaded_dicom_files = sorted([os.path.join(self.filename, file) for file in os.listdir(self.filename)
                                              if file.endswith('.dcm')])

        '''
        AppWindow.count = AppWindow.count + 1
        self.filename = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

        if self.filename:
            self.vtk(self.filename)
            self.vtkWidget = self.vtkWidget  # Update vtkWidget when DICOM file is loaded

        
        AppWindow.count = AppWindow.count + 1
        self.filename = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')

        if self.filename:
            self.vtk(self.filename)
            '''
    
    def apply_colormap(self, colormap_name):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap=colormap_name)
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion
                colormap_image = cv2.applyColorMap(dicom_image, getattr(cv2, f'COLORMAP_{colormap_name.upper()}'))

                # Display the colormap image
                matplotlib_widget.ax.imshow(colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle(f"DICOM Image with {colormap_name.capitalize()} Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                if file.endswith('.dcm')])
                self.apply_colormap(colormap_name)


    '''
    def autumn_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='autumn')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)
                    
                # Perform colormap conversion (e.g., to 'hsv')
                autumn_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_AUTUMN)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(autumn_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Autumn Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.autumn_colormap()

    def bone_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='bone')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                bone_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_BONE)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(bone_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Bone Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.bone_colormap()

    def jet_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='jet')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                jet_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_JET)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(jet_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Jet Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.jet_colormap()

    def rainbow_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='rainbow')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                rainbow_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_RAINBOW)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(rainbow_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Rainbow Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.rainbow_colormap()

    def ocean_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='ocean')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)
                    
                # Perform colormap conversion (e.g., to 'hsv')
                ocean_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_OCEAN)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(ocean_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Ocean Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.ocean_colormap()

    def summer_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='summer')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                summer_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_SUMMER)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(summer_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Summer Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.summer_colormap()

    def spring_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='spring')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                spring_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_SPRING)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(spring_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Spring Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.spring_colormap()
    
    def cool_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='cool')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                cool_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_COOL)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(cool_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Cool Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.cool_colormap()

    def hsv_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='hsv')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                hsv_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_HSV)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(hsv_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with HSV Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.hsv_colormap()
    
    def hot_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='hot')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                hot_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_HOT)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(hot_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Hot Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.hot_colormap()

    def magma_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='magma')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                magma_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_MAGMA)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(magma_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Magma Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.magma_colormap()
    
    def twilight_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='twilight')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                twilight_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_TWILIGHT)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(twilight_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Twilight Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.twilight_colormap()

    def turbo_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='turbo')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                turbo_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_TURBO)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(turbo_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Turbo Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.turbo_colormap()

    def winter_colormap(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='winter')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Convert dicom_image to a suitable format (CV_8UC1 or CV_8UC3)
                if dicom_image.dtype != np.uint8:
                    dicom_image = ((dicom_image - np.min(dicom_image)) / (np.max(dicom_image) - np.min(dicom_image)) * 255).astype(np.uint8)

                # Perform colormap conversion (e.g., to 'hsv')
                winter_colormap_image = cv2.applyColorMap(dicom_image, cv2.COLORMAP_WINTER)

                # Display the HSV colormap image
                matplotlib_widget.ax.imshow(winter_colormap_image)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with Winter Colormap")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.winter_colormap()

    '''

    def hsv_colormap_dicom(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap='hsv')
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_data(dicom_image)

                # Perform colormap conversion (e.g., to 'hsv')
                hsv_colormap_image = cv2.cvtColor(dicom_image, cv2.COLOR_GRAY2BGR)
                hsv_colormap_image2 = cv2.cvtColor(hsv_colormap_image, cv2.COLOR_BGR2HSV)

                # Display the HSV colormap image
                
                #matplotlib_widget.ax.set_title(f"Slice: {slice_index}")
                matplotlib_widget.ax.imshow(hsv_colormap_image2)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)  # Use the canvas as the widget
            sub_window.setWindowTitle("DICOM Image with HSV Colormap & Slider")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()

        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.hsv_colormap_dicom()  # Re-run hsv_colormap_dicom() for HSV colormap conversion

    def canny_edge(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap=cm.gray)
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_array(dicom_image)

                # Apply Canny edge detection on the selected DICOM slice
                canny_edges = cv2.Canny(dicom_image.astype(np.uint8), 400, 500)  # Apply Canny edge detection
                if hasattr(update, 'edge_plot'):
                    update.edge_plot.set_array(canny_edges)
                else:
                    update.edge_plot = matplotlib_widget.ax.imshow(canny_edges, cmap=cm.gray, alpha=0.5)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)
            sub_window.setWindowTitle("DICOM Image with Canny Edges & Slider")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()
        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                  if file.endswith('.dcm')])
                self.canny_edge()  # Re-run canny_edge() to display the Canny edge
                     
    def sobel_edge(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap=cm.gray)
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_array(dicom_image)

                # Apply Sobel edge detection on the selected DICOM slice
                sobel_x = cv2.Sobel(dicom_image, cv2.CV_64F, 1, 0, ksize=5)  # Sobel in X direction
                sobel_y = cv2.Sobel(dicom_image, cv2.CV_64F, 0, 1, ksize=5)  # Sobel in Y direction
                sobel_edges = np.sqrt(sobel_x**2 + sobel_y**2)  # Combined Sobel edges magnitude
                sobel_edges = np.uint8(255 * sobel_edges / np.max(sobel_edges))  # Normalize for display
                sobel_edges = cv2.cvtColor(sobel_edges, cv2.COLOR_GRAY2RGB)  # Convert to RGB for display
                matplotlib_widget.ax.imshow(sobel_edges)

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)
            sub_window.setWindowTitle("DICOM Image with Sobel Edges & Slider")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()
        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                if file.endswith('.dcm')])
                self.sobel_edge()  # Re-run sobel_edge() to display the Sobel edges
    
    def prewitt_edge(self):
        if self.loaded_dicom_files:
            num_slices = len(self.loaded_dicom_files)
            first_dicom = pydicom.dcmread(self.loaded_dicom_files[0])
            dicom_image = first_dicom.pixel_array

            # Create Matplotlib widget and other necessary components
            matplotlib_widget = MatplotlibWidget()
            img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap=cm.gray)
            ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
            matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

            def update(val):
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array

                # Define Prewitt kernels
                kernelx = np.array([[1, 1, 1], [0, 0, 0], [-1, -1, -1]])
                kernely = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])

                # Apply Prewitt edge detection using filter2D
                img_prewittx = cv2.filter2D(dicom_image, -1, kernelx)
                img_prewitty = cv2.filter2D(dicom_image, -1, kernely)
                
                # Combine Prewitt edges
                img_prewitt = img_prewittx + img_prewitty

                # Display the Prewitt edges using Matplotlib
                matplotlib_widget.ax.imshow(img_prewitt, cmap=cm.gray)
                '''
                slice_index = int(round(matplotlib_widget.slider.val))
                dicom_data = pydicom.dcmread(self.loaded_dicom_files[slice_index])
                dicom_image = dicom_data.pixel_array
                img_plot.set_array(dicom_image)
                
                
                # Apply Prewitt edge detection on the selected DICOM slice
                prewitt_kernel_x = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])  # Prewitt kernel in X direction
                prewitt_kernel_y = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])  # Prewitt kernel in Y direction
                prewitt_x = cv2.filter2D(dicom_image, -1, prewitt_kernel_x)
                prewitt_y = cv2.filter2D(dicom_image, -1, prewitt_kernel_y)
                prewitt_edges = np.sqrt(prewitt_x ** 2 + prewitt_y ** 2)  # Combined Prewitt edges magnitude
                prewitt_edges = np.uint8(255 * prewitt_edges / np.max(prewitt_edges))  # Normalize for display
                matplotlib_widget.ax.imshow(prewitt_edges, cmap=cm.gray)
                '''

            matplotlib_widget.slider.on_changed(update)

            sub_window = QtWidgets.QMdiSubWindow(self.mdi)
            sub_window.setWidget(matplotlib_widget)
            sub_window.setWindowTitle("DICOM Image with Prewitt Edges & Slider")
            self.mdi.addSubWindow(sub_window)
            sub_window.show()
        else:
            # If no DICOM files are loaded, prompt the user to select a DICOM directory
            selected_directory = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select DICOM Directory')

            if selected_directory:
                self.loaded_dicom_files = sorted([os.path.join(selected_directory, file) for file in os.listdir(selected_directory)
                                                if file.endswith('.dcm')])
                self.prewitt_edge()  # Re-run prewitt_edge() to display the Prewitt edges

    def vtk(self, filename):
        self.sub = QMdiSubWindow()
        self.frame = QFrame()

        #self.add_dataset(filename)
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.sub.setWidget(self.vtkWidget)
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(0.2, 0.2, 0.2)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Set the interactor style to vtkInteractorStyleTrackballCamera
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(style)

        # Set Titlebar
        self.sub.setWindowTitle("Dataset " + str(AppWindow.count))

        self.imageData = vtk.vtkImageData()
        self.reader = vtk.vtkDICOMImageReader()

        self.volumeMapper = vtk.vtkSmartVolumeMapper()
        self.volumeProperty = vtk.vtkVolumeProperty()
        self.gradientOpacity = vtk.vtkPiecewiseFunction()
        self.scalarOpacity = vtk.vtkPiecewiseFunction()
        self.color = vtk.vtkColorTransferFunction()
        self.volume = vtk.vtkVolume()
        self.interactorStyle = vtk.vtkInteractorStyleTrackballCamera()
        self.reader.SetDirectoryName(filename)
        self.reader.SetDataScalarTypeToUnsignedShort()
        self.reader.UpdateWholeExtent()
        self.reader.Update()
        self.imageData.ShallowCopy(self.reader.GetOutput())

        self.volumeMapper.SetBlendModeToComposite()
        self.volumeMapper.SetRequestedRenderModeToGPU()
        self.volumeMapper.SetInputData(self.imageData)
        self.volumeProperty.ShadeOn()
        self.volumeProperty.SetInterpolationTypeToLinear()
        self.volumeProperty.SetAmbient(0.1)
        self.volumeProperty.SetDiffuse(0.9)
        self.volumeProperty.SetSpecular(0.2)
        self.volumeProperty.SetSpecularPower(10.0)
        self.gradientOpacity.AddPoint(0.0, 0.0)
        self.gradientOpacity.AddPoint(2000.0, 1.0)
        self.volumeProperty.SetGradientOpacity(self.gradientOpacity)
        self.scalarOpacity.AddPoint(-800.0, 0.0)
        self.scalarOpacity.AddPoint(-750.0, 1.0)
        self.scalarOpacity.AddPoint(-350.0, 1.0)
        self.scalarOpacity.AddPoint(-300.0, 0.0)
        self.scalarOpacity.AddPoint(-200.0, 0.0)
        self.scalarOpacity.AddPoint(-100.0, 1.0)
        self.scalarOpacity.AddPoint(1000.0, 0.0)
        self.scalarOpacity.AddPoint(2750.0, 0.0)
        self.scalarOpacity.AddPoint(2976.0, 1.0)
        self.scalarOpacity.AddPoint(3000.0, 0.0)
        self.volumeProperty.SetScalarOpacity(self.scalarOpacity)
        self.color.AddRGBPoint(-750.0, 0.08, 0.05, 0.03)
        self.color.AddRGBPoint(-350.0, 0.39, 0.25, 0.16)
        self.color.AddRGBPoint(-200.0, 0.80, 0.80, 0.80)
        self.color.AddRGBPoint(2750.0, 0.70, 0.70, 0.70)
        self.color.AddRGBPoint(3000.0, 0.35, 0.35, 0.35)
        self.volumeProperty.SetColor(self.color)
        self.volume.SetMapper(self.volumeMapper)
        self.volume.SetProperty(self.volumeProperty)
        self.ren.AddVolume(self.volume)
        self.ren.ResetCamera()

        self.mdi.addSubWindow(self.sub)
        self.sub.show()
        self.iren.Initialize()
        self.iren.Start()

    def axial_dicom(self):
        # Open a dialog to select a DICOM directory
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        if file_dialog.exec_():
            selected_directory = file_dialog.selectedFiles()
            if selected_directory:
                dicom_folder = selected_directory[0]
                # Load all DICOM files from the selected directory
                dicom_files = sorted([os.path.join(dicom_folder, file) for file in os.listdir(dicom_folder)
                                    if file.endswith('.dcm')])

                if dicom_files:
                    # Read the first DICOM file to get the shape
                    first_dicom = pydicom.dcmread(dicom_files[0])
                    num_slices = len(dicom_files)
                    dicom_image = first_dicom.pixel_array

                    # Create a Matplotlib widget
                    matplotlib_widget = MatplotlibWidget()
                    img_plot = matplotlib_widget.ax.imshow(dicom_image, cmap=cm.gray)
                    ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
                    matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, num_slices - 1, valinit=0, valstep=1, valfmt='%d')

                    def update(val):
                        slice_index = int(round(matplotlib_widget.slider.val))
                        dicom_data = pydicom.dcmread(dicom_files[slice_index])
                        img_plot.set_array(dicom_data.pixel_array)
                    
                    matplotlib_widget.slider.on_changed(update)

                    sub_window = QMdiSubWindow(self.mdi)
                    sub_window.setWidget(matplotlib_widget)
                    sub_window.setWindowTitle("DICOM Image")
                    self.mdi.addSubWindow(sub_window)
                    sub_window.show()
    
    def coronal_dicom(self):
        # Open a dialog to select a DICOM directory
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        if file_dialog.exec_():
            selected_directory = file_dialog.selectedFiles()
            if selected_directory:
                dicom_folder = selected_directory[0]
                # Load all DICOM files from the selected directory
                dicom_files = sorted([os.path.join(dicom_folder, file) for file in os.listdir(dicom_folder)
                                    if file.endswith('.dcm')])

                if dicom_files:
                    # Read the first DICOM file to get the shape
                    first_dicom = pydicom.dcmread(dicom_files[0])
                    #num_slices = len(dicom_files)
                    dicom_image_shape = first_dicom.pixel_array
                    coronal_images = np.zeros((first_dicom.pixel_array.shape[1], len(dicom_files)))

                    # Iterate through DICOM files and extract the coronal slices
                    for idx, file in enumerate(dicom_files):
                        dicom_data = pydicom.dcmread(file)
                        coronal_images[:, idx] = dicom_data.pixel_array[:, 0]

                    # Create a Matplotlib widget
                    matplotlib_widget = MatplotlibWidget()
                    img_plot = matplotlib_widget.ax.imshow(coronal_images, cmap=cm.gray, aspect='auto', interpolation='nearest')
                    #figure.colorbar(img_plot, ax=self.ax)
                    ax_slider = plt.axes([0.1, 0.02, 0.8, 0.03])
                    matplotlib_widget.slider = Slider(ax_slider, 'Slice', 0, len(dicom_files) - 1, valinit=0, valstep=1, valfmt='%d')

                    def update(val):
                        slice_index = int(round(matplotlib_widget.slider.val))
                        matplotlib_widget.ax.images[0].set_array(coronal_images[:, slice_index])
                        matplotlib_widget.canvas.draw_idle()

                    matplotlib_widget.slider.on_changed(update)

                    sub_window = QMdiSubWindow(self.mdi)
                    sub_window.setWidget(matplotlib_widget)
                    sub_window.setWindowTitle("DICOM Image")
                    self.mdi.addSubWindow(sub_window)
                    sub_window.show()

    def sagittal_dicom(self):
        pass

    def docker_widget(self):      
        dockWid = QDockWidget('Tool', self)
        #dockWid.setStyleSheet("font-size: 20px; font-family: Arial; ; font-weight: bold")
        dockWid.setMaximumWidth(400)
        dockWid.setMinimumWidth(300)
        
        layout = QGridLayout()
        
        toolbox = QToolBox()
        layout.addWidget(toolbox, 0, 0)

        # TAB TRANSFORMATION
        w1 = QWidget()
        scale = QLabel('Scale')
        sx_coord = QLabel('X')
        sy_coord = QLabel('Y')
        sz_coord = QLabel('Z')
        rotate = QLabel('Rotate')
        rx_coord = QLabel('X')
        ry_coord = QLabel('Y')
        rz_coord = QLabel('Z')
        translate = QLabel('Translate')
        tx_coord = QLabel('X')
        ty_coord = QLabel('Y')
        tz_coord = QLabel('Z')

        self.scaleX = QLineEdit(self)
        self.scaleY = QLineEdit(self)
        self.scaleZ = QLineEdit(self)
        scalee = QPushButton('Apply', self)
        scalee.clicked.connect(self.scaleXYZ)
        self.scaleX.setFixedWidth(30)
        self.scaleY.setFixedWidth(30)
        self.scaleZ.setFixedWidth(30)
        self.rotateX = QLineEdit(self)
        self.rotateY = QLineEdit(self)
        self.rotateZ = QLineEdit(self)
        rotatee = QPushButton('Apply', self)
        rotatee.clicked.connect(self.rotateXYZ)
        self.rotateX.setFixedWidth(30)
        self.rotateY.setFixedWidth(30)
        self.rotateZ.setFixedWidth(30)
        self.translateX = QLineEdit()
        self.translateY = QLineEdit()
        self.translateZ = QLineEdit()
        self.translateX.setFixedWidth(30)
        self.translateY.setFixedWidth(30)
        self.translateZ.setFixedWidth(30)
        translatee = QPushButton('Apply', self)
        translatee.clicked.connect(self.translateXYZ)

        grid = QGridLayout()
        grid.setSpacing(5)

        grid.addWidget(scale, 1, 0)
        grid.addWidget(sx_coord, 1, 1)
        grid.addWidget(self.scaleX, 1, 2)
        grid.addWidget(sy_coord, 1, 3)
        grid.addWidget(self.scaleY, 1, 4)
        grid.addWidget(sz_coord, 1, 5)
        grid.addWidget(self.scaleZ, 1, 6)
        grid.addWidget(scalee, 1, 7)

        grid.addWidget(rotate, 2, 0)
        grid.addWidget(rx_coord, 2, 1)
        grid.addWidget(self.rotateX, 2, 2)
        grid.addWidget(ry_coord, 2, 3)
        grid.addWidget(self.rotateY, 2, 4)
        grid.addWidget(rz_coord, 2, 5)
        grid.addWidget(self.rotateZ, 2, 6)
        grid.addWidget(rotatee, 2, 7)

        grid.addWidget(translate, 3, 0)
        grid.addWidget(tx_coord, 3, 1)
        grid.addWidget(self.translateX, 3, 2)
        grid.addWidget(ty_coord, 3, 3)
        grid.addWidget(self.translateY, 3, 4)
        grid.addWidget(tz_coord, 3, 5)
        grid.addWidget(self.translateZ, 3, 6)
        grid.addWidget(translatee, 3, 7)
        w1.setLayout(grid)

        toolbox.addItem(w1, 'Transformation')

        # TAB EDGE DETECTION
        w2 = QWidget()
        grid_edge = QGridLayout()
        grid_edge.setSpacing(10)

        canny = QPushButton('Canny Edge Detection', self)
        canny.clicked.connect(self.canny_edge)
        sobel = QPushButton('Sobel Edge Detection', self)
        sobel.clicked.connect(self.sobel_edge)
        prewitt = QPushButton('Prewitt Edge Detection', self)
        prewitt.clicked.connect(self.prewitt_edge)

        grid_edge.addWidget(canny, 0, 0)
        grid_edge.addWidget(sobel, 1, 0)
        grid_edge.addWidget(prewitt, 2, 0)

        w2.setLayout(grid_edge)
        toolbox.addItem(w2, 'Edge Detection')

        # TAB COLOMAP
        w3 = QWidget()
        grid_color = QGridLayout()
        grid_color.setSpacing(10)

        autumn = QPushButton('Autumn', self)
        autumn.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_autumn.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        autumn.clicked.connect(lambda: self.apply_colormap('autumn'))

        bone = QPushButton('Bone', self)
        bone.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_bone.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        bone.clicked.connect(lambda: self.apply_colormap('bone'))

        jet = QPushButton('Jet', self)
        jet.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_jet.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        jet.clicked.connect(lambda: self.apply_colormap('jet'))

        rainbow = QPushButton('Rainbow', self)
        rainbow.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_rainbow.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        rainbow.clicked.connect(lambda: self.apply_colormap('rainbow'))

        ocean = QPushButton('Ocean', self)
        ocean.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_ocean.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        ocean.clicked.connect(lambda: self.apply_colormap('ocean'))

        summer = QPushButton('Summer', self)
        summer.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_summer.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        summer.clicked.connect(lambda: self.apply_colormap('summer'))

        spring = QPushButton('Spring', self)
        spring.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_spring.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        spring.clicked.connect(lambda: self.apply_colormap('spring'))

        cool = QPushButton('Cool', self)
        cool.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_cool.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        cool.clicked.connect(lambda: self.apply_colormap('cool'))

        hsv = QPushButton('HSV', self)
        hsv.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_hsv.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        hsv.clicked.connect(lambda: self.apply_colormap('hsv'))

        hot = QPushButton('Hot', self)
        hot.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_hot.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        hot.clicked.connect(lambda: self.apply_colormap('hot'))

        magma = QPushButton('Magma', self)
        magma.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_magma.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        magma.clicked.connect(lambda: self.apply_colormap('magma'))

        twilight = QPushButton('Twilight', self)
        twilight.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_twilight.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        twilight.clicked.connect(lambda: self.apply_colormap('twilight'))

        turbo = QPushButton('Turbo', self)
        turbo.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_turbo.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        turbo.clicked.connect(lambda: self.apply_colormap('turbo'))

        winter = QPushButton('Winter', self)
        winter.setStyleSheet(
            "QPushButton {"
            "   border-image: url('icon_ass2/colorscale_winter.jpg');"
            "   font: bold 10pt Arial;"
            "   min-width: 100px;"
            "   min-height: 50px;"
            "}"
        )
        winter.clicked.connect(lambda: self.apply_colormap('winter'))

        grid_color.addWidget(spring, 0, 0)
        grid_color.addWidget(summer, 1, 0)
        grid_color.addWidget(autumn, 2, 0)
        grid_color.addWidget(winter, 3, 0)
        grid_color.addWidget(bone, 4, 0)
        grid_color.addWidget(jet, 5, 0)
        grid_color.addWidget(rainbow, 6, 0)
        grid_color.addWidget(ocean, 7, 0)
        grid_color.addWidget(cool, 8, 0)
        grid_color.addWidget(hsv, 9, 0)
        grid_color.addWidget(hot, 10, 0)
        grid_color.addWidget(magma, 11, 0)
        grid_color.addWidget(twilight, 12, 0)
        grid_color.addWidget(turbo, 13, 0)

        w3.setLayout(grid_color)
        toolbox.addItem(w3, 'Colormap')

        # TAB WIDGET
        w4 = QWidget()
        grid_w = QGridLayout()
        grid_w.setSpacing(10)

        axis = QCheckBox('3D Axis', self)
        axis.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'icon_ass2', '3d.png')))
        axis.clicked.connect(self.thrDaxis)
        box = QCheckBox('3D Box', self)
        box.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'icon_ass2', 'cube.png')))
        box.clicked.connect(self.thrBox)

        grid_w.addWidget(axis, 0, 0)
        grid_w.addWidget(box, 0, 1)

        w4.setLayout(grid_w)
        toolbox.addItem(w4, 'Widget')

        

        font = QtGui.QFont()
        font.setFamily("Arial")  # Set the font family (e.g., Arial, Helvetica, etc.)
        font.setPointSize(10)    # Set the font size to 10 (adjust as needed)
        font.setBold(True)       # Make the text bold

        toolbox.setFont(font)
        dockWid.setFont(font)

        # Apply the font to specific QLabel widgets
        scale.setFont(font)
        sx_coord.setFont(font)
        sy_coord.setFont(font)
        sz_coord.setFont(font)
        rotate.setFont(font)
        rx_coord.setFont(font)
        ry_coord.setFont(font)
        rz_coord.setFont(font)
        translate.setFont(font)
        tx_coord.setFont(font)
        ty_coord.setFont(font)
        tz_coord.setFont(font)

        # Apply the font to specific QPushButton widgets
        scalee.setFont(font)
        rotatee.setFont(font)
        translatee.setFont(font)

        dockWid.setWidget(toolbox)
        dockWid.setFloating(False)
        dockWid.setFeatures(dockWid.features() & ~QDockWidget.DockWidgetClosable)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWid)          

    def thrDaxis(self, checked):
        if checked:
            axesActor = vtk.vtkAxesActor()
            self.axes = vtk.vtkOrientationMarkerWidget()
            self.axes.SetOrientationMarker(axesActor)
            self.axes.SetInteractor(self.iren)
            self.axes.EnabledOn()
            self.axes.InteractiveOn()
            self.ren.ResetCamera()
            self.show()
            self.iren.Initialize()
        else:
            # If the axis is unchecked, disable it
            if hasattr(self, 'axes'):
                self.axes.EnabledOff()
                self.ren.Render()
                self.show()
                self.iren.Initialize()

    def thrBox(self):
        outline = vtk.vtkOutlineFilter()
        outline.SetInputConnection(self.reader.GetOutputPort())

        outlineMapper = vtk.vtkPolyDataMapper()
        outlineMapper.SetInputConnection(outline.GetOutputPort())

        self.outlineActor = vtk.vtkActor()
        self.outlineActor.SetMapper(outlineMapper)
        self.outlineActor.GetProperty().SetColor(1, 1, 1)
        self.ren.AddActor(self.outlineActor)
        self.ren.ResetCamera()

        self.show()
        self.iren.Initialize()

    def scaleXYZ(self):
        x = int(self.scaleX.text())
        y = int(self.scaleY.text())
        z = int(self.scaleZ.text())
        # print(x, y, z)
        # self.volume.SetOrientation(x, y, z)
        self.ren.Render()
        self.ren.EraseOff()
        self.outlineActor.SetScale(x, y, z)
        self.volume.SetScale(x, y, z)
        self.ren.Render()
        self.ren.EraseOn()

    def rotateXYZ(self):
        x = int(self.rotateX.text())
        y = int(self.rotateY.text())
        z = int(self.rotateZ.text())
        self.outlineActor.SetOrientation(x, y, z)
        self.volume.SetOrientation(x, y, z)
        self.ren.Render()
        self.ren.EraseOff()

        self.volume.RotateX(x)
        self.volume.RotateY(y)
        self.volume.RotateZ(z)
        self.outlineActor.RotateX(x)
        self.outlineActor.RotateY(y)
        self.outlineActor.RotateZ(z)

        self.ren.Render()
        self.ren.EraseOn()

    def translateXYZ(self):
        x = int(self.translateX.text())
        y = int(self.translateY.text())
        z = int(self.translateZ.text())
        # self.volume.SetOrientation(0, 0, 0)
        self.ren.Render()
        self.ren.EraseOff()
        self.outlineActor.SetPosition(x, y, z)
        self.volume.SetPosition(x, y, z)
        self.ren.Render()
        self.ren.EraseOn()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Set Fusion style for modern look
    app_win = AppWindow()
    sys.exit(app.exec())
/*==============================================================================

  Copyright (c) Kitware, Inc.

  See http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Julien Finet, Kitware, Inc.
  and was partially funded by NIH grant 3P41RR013218-12S1

==============================================================================*/

// AIGSlicer includes
#include "qAIGSlicerAppMainWindow.h"
#include "qAIGSlicerAppMainWindow_p.h"

// Qt includes
#include <QDesktopWidget>
#include <QLabel>

// Slicer includes
#include "qSlicerApplication.h"
#include "qSlicerAboutDialog.h"
#include "qSlicerMainWindow_p.h"
#include "qSlicerModuleSelectorToolBar.h"
#include "qMRMLWidget.h"

//-----------------------------------------------------------------------------
// qAIGSlicerAppMainWindowPrivate methods

qAIGSlicerAppMainWindowPrivate::qAIGSlicerAppMainWindowPrivate(qAIGSlicerAppMainWindow& object)
  : Superclass(object)
{
}

//-----------------------------------------------------------------------------
qAIGSlicerAppMainWindowPrivate::~qAIGSlicerAppMainWindowPrivate()
{
}

//-----------------------------------------------------------------------------
void qAIGSlicerAppMainWindowPrivate::init()
{
#if (QT_VERSION >= QT_VERSION_CHECK(5, 7, 0))
  QApplication::setAttribute(Qt::AA_UseHighDpiPixmaps);
#endif
  Q_Q(qAIGSlicerAppMainWindow);
  this->Superclass::init();
}

//-----------------------------------------------------------------------------
void qAIGSlicerAppMainWindowPrivate::setupUi(QMainWindow * mainWindow)
{
  qSlicerApplication * app = qSlicerApplication::application();

  //----------------------------------------------------------------------------
  // Add actions
  //----------------------------------------------------------------------------
  QAction* helpAboutSlicerAppAction = new QAction(mainWindow);
  helpAboutSlicerAppAction->setObjectName("HelpAboutAIGSlicerAppAction");
  helpAboutSlicerAppAction->setText(qAIGSlicerAppMainWindow::tr("About %1").arg(qSlicerApplication::application()->mainApplicationDisplayName()));

  //----------------------------------------------------------------------------
  // Calling "setupUi()" after adding the actions above allows the call
  // to "QMetaObject::connectSlotsByName()" done in "setupUi()" to
  // successfully connect each slot with its corresponding action.
  this->Superclass::setupUi(mainWindow);

  // Add Help Menu Action
  this->HelpMenu->addAction(helpAboutSlicerAppAction);

  //----------------------------------------------------------------------------
  // Configure
  //----------------------------------------------------------------------------
  mainWindow->setWindowIcon(QIcon(":/Icons/Medium/DesktopIcon.png"));

  // Create an empty widget for the title bar to avoid blocking GUI
  QWidget* titleBarWidget = new QWidget();
  titleBarWidget->setObjectName("LogoLabel");
  this->PanelDockWidget->setTitleBarWidget(titleBarWidget);

  // Hide the menus
  //this->menubar->setVisible(false);
  //this->FileMenu->setVisible(false);
  //this->EditMenu->setVisible(false);
  //this->ViewMenu->setVisible(false);
  //this->LayoutMenu->setVisible(false);
  //this->HelpMenu->setVisible(false);
}

//-----------------------------------------------------------------------------
// qAIGSlicerAppMainWindow methods

//-----------------------------------------------------------------------------
qAIGSlicerAppMainWindow::qAIGSlicerAppMainWindow(QWidget* windowParent)
  : Superclass(new qAIGSlicerAppMainWindowPrivate(*this), windowParent)
{
  Q_D(qAIGSlicerAppMainWindow);
  d->init();
}

//-----------------------------------------------------------------------------
qAIGSlicerAppMainWindow::qAIGSlicerAppMainWindow(
  qAIGSlicerAppMainWindowPrivate* pimpl, QWidget* windowParent)
  : Superclass(pimpl, windowParent)
{
  // init() is called by derived class.
}

//-----------------------------------------------------------------------------
qAIGSlicerAppMainWindow::~qAIGSlicerAppMainWindow()
{
}

//-----------------------------------------------------------------------------
void qAIGSlicerAppMainWindow::on_HelpAboutAIGSlicerAppAction_triggered()
{
  qSlicerAboutDialog about(this);
  about.setLogo(QPixmap(":/Logo.png"));
  about.exec();
}

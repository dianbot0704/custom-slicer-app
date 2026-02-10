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

// AksaratorApp includes
#include "qAksaratorAppMainWindow.h"
#include "qAksaratorAppMainWindow_p.h"

// Qt includes
#include <QDesktopWidget>
#include <QLabel>
#include <QTimer>

// Slicer includes
#include "qSlicerApplication.h"
#include "qSlicerAboutDialog.h"
#include "qSlicerMainWindow_p.h"
#include "qSlicerModuleSelectorToolBar.h"
#include "qMRMLWidget.h"

//-----------------------------------------------------------------------------
// qAksaratorAppMainWindowPrivate methods

qAksaratorAppMainWindowPrivate::qAksaratorAppMainWindowPrivate(qAksaratorAppMainWindow& object)
  : Superclass(object)
{
}

//-----------------------------------------------------------------------------
qAksaratorAppMainWindowPrivate::~qAksaratorAppMainWindowPrivate()
{
}

//-----------------------------------------------------------------------------
void qAksaratorAppMainWindowPrivate::init()
{
#if (QT_VERSION >= QT_VERSION_CHECK(5, 7, 0))
  QApplication::setAttribute(Qt::AA_UseHighDpiPixmaps);
#endif
  Q_Q(qAksaratorAppMainWindow);
  this->Superclass::init();
}

//-----------------------------------------------------------------------------
void qAksaratorAppMainWindowPrivate::setupUi(QMainWindow * mainWindow)
{
  qSlicerApplication * app = qSlicerApplication::application();
  const QString startupModuleName = QStringLiteral("IntraopPlanner");

  //----------------------------------------------------------------------------
  // Add actions
  //----------------------------------------------------------------------------
  QAction* helpAboutSlicerAppAction = new QAction(mainWindow);
  helpAboutSlicerAppAction->setObjectName("HelpAboutAksaratorAppAction");
  helpAboutSlicerAppAction->setText(qAksaratorAppMainWindow::tr("About %1").arg(qSlicerApplication::application()->mainApplicationDisplayName()));

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

  // Force startup module selection regardless of persisted user settings.
  QObject::connect(app, &qSlicerApplication::startupCompleted, mainWindow,
    [this, startupModuleName]()
    {
      if (this->ModuleSelectorToolBar)
        {
        this->ModuleSelectorToolBar->selectModule(startupModuleName);
        }
    });
  QTimer::singleShot(0, mainWindow,
    [this, startupModuleName]()
    {
      if (this->ModuleSelectorToolBar)
        {
        this->ModuleSelectorToolBar->selectModule(startupModuleName);
        }
    });
}

//-----------------------------------------------------------------------------
// qAksaratorAppMainWindow methods

//-----------------------------------------------------------------------------
qAksaratorAppMainWindow::qAksaratorAppMainWindow(QWidget* windowParent)
  : Superclass(new qAksaratorAppMainWindowPrivate(*this), windowParent)
{
  Q_D(qAksaratorAppMainWindow);
  d->init();
}

//-----------------------------------------------------------------------------
qAksaratorAppMainWindow::qAksaratorAppMainWindow(
  qAksaratorAppMainWindowPrivate* pimpl, QWidget* windowParent)
  : Superclass(pimpl, windowParent)
{
  // init() is called by derived class.
}

//-----------------------------------------------------------------------------
qAksaratorAppMainWindow::~qAksaratorAppMainWindow()
{
}

//-----------------------------------------------------------------------------
void qAksaratorAppMainWindow::setHomeModuleCurrent()
{
  Q_D(qAksaratorAppMainWindow);
  const QString startupModuleName = QStringLiteral("IntraopPlanner");
  if (d->ModuleSelectorToolBar)
    {
    d->ModuleSelectorToolBar->selectModule(startupModuleName);
    return;
    }
  this->Superclass::setHomeModuleCurrent();
}

//-----------------------------------------------------------------------------
void qAksaratorAppMainWindow::on_HelpAboutAksaratorAppAction_triggered()
{
  qSlicerAboutDialog about(this);
  about.setLogo(QPixmap(":/Logo.png"));
  about.exec();
}

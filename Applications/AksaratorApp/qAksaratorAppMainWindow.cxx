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
#include <QAction>
#include <QCloseEvent>
#include <QCoreApplication>
#include <QCryptographicHash>
#include <QDebug>
#include <QDesktopWidget>
#include <QInputDialog>
#include <QLabel>
#include <QLineEdit>
#include <QMenuBar>
#include <QMessageBox>
#include <QSettings>
#include <QShortcut>
#include <QShowEvent>
#include <QStatusBar>
#include <QTimer>
#include <QToolBar>

// Slicer includes
#include "qSlicerApplication.h"
#include "qSlicerAboutDialog.h"
#include "qSlicerMainWindow_p.h"
#include "qSlicerModuleSelectorToolBar.h"
#include "qMRMLWidget.h"

namespace
{
const char KioskArgument[] = "--kiosk";
const char KioskEnvironmentVariable[] = "AKSARATOR_KIOSK";
// Optional settings, read from the user settings file.
const char KioskUnlockShortcutSettingsKey[] = "Kiosk/UnlockShortcut";
const char KioskUnlockPinSha256SettingsKey[] = "Kiosk/UnlockPinSha256";
const char KioskDefaultUnlockShortcut[] = "Ctrl+Alt+Shift+K";
} // end of anonymous namespace

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
  this->Superclass::init();

  // Lock before the window is first shown, so it opens fullscreen and the
  // Slicer menus and toolbars never flash on screen.
  if (qAksaratorAppMainWindow::isKioskModeRequested())
    {
    this->setKioskMode(true);
    }
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
void qAksaratorAppMainWindowPrivate::hideSlicerChrome()
{
  Q_Q(qAksaratorAppMainWindow);
  q->menuBar()->hide();
  q->statusBar()->hide();
  for (QToolBar* toolBar : q->findChildren<QToolBar*>())
    {
    toolBar->hide();
    }
  for (QDockWidget* dockWidget : q->findChildren<QDockWidget*>())
    {
    if (dockWidget != this->PanelDockWidget)
      {
      dockWidget->hide();
      }
    }
}

//-----------------------------------------------------------------------------
void qAksaratorAppMainWindowPrivate::setKioskMode(bool enable)
{
  Q_Q(qAksaratorAppMainWindow);
  if (this->KioskMode == enable)
    {
    return;
    }
  this->KioskMode = enable;

  if (enable)
    {
    // Slicer's own shortcuts open the Python console (Ctrl+3), the error log
    // (Ctrl+0), the module finder (Ctrl+F), switch modules (Ctrl+Left/Right),
    // hide the module panel (Ctrl+5) and trigger menu items. Only Slicer's
    // actions exist this early; module widgets are created later and keep
    // their shortcuts.
    this->KioskSavedShortcuts.clear();
    for (QAction* action : q->findChildren<QAction*>())
      {
      if (!action->shortcuts().isEmpty())
        {
        this->KioskSavedShortcuts.append(qMakePair(QPointer<QAction>(action), action->shortcuts()));
        action->setShortcuts(QList<QKeySequence>());
        }
      }

    this->hideSlicerChrome();
    // The module panel holds the workflow: it must not be closed, moved or floated.
    this->KioskSavedPanelFeatures = this->PanelDockWidget->features();
    this->PanelDockWidget->setFeatures(QDockWidget::NoDockWidgetFeatures);
    // Dropping a file on the window would load it into the scene.
    q->setAcceptDrops(false);

    if (!this->KioskUnlockShortcut)
      {
      QSettings settings;
      const QKeySequence unlockKeys(
        settings.value(KioskUnlockShortcutSettingsKey, KioskDefaultUnlockShortcut).toString());
      this->KioskUnlockShortcut = new QShortcut(unlockKeys, q);
      QObject::connect(this->KioskUnlockShortcut, &QShortcut::activated,
        q, &qAksaratorAppMainWindow::requestKioskUnlock);
      }
    this->KioskUnlockShortcut->setEnabled(true);

    if (q->isVisible())
      {
      q->showFullScreen();
      }
    else
      {
      q->setWindowState(q->windowState() | Qt::WindowFullScreen);
      }
    qDebug() << "Kiosk mode enabled; unlock with" << this->KioskUnlockShortcut->key().toString();
    }
  else
    {
    for (const auto& savedShortcut : this->KioskSavedShortcuts)
      {
      if (savedShortcut.first)
        {
        savedShortcut.first->setShortcuts(savedShortcut.second);
        }
      }
    this->KioskSavedShortcuts.clear();

    this->PanelDockWidget->setFeatures(this->KioskSavedPanelFeatures);
    q->setAcceptDrops(true);
    if (this->KioskUnlockShortcut)
      {
      this->KioskUnlockShortcut->setEnabled(false);
      }

    // Bring back the toolbars and docks as they were before locking. A module
    // that hides Slicer's UI itself (such as IntraopPlanner) may hide them again.
    q->restoreState(this->StartupState);
    q->menuBar()->show();
    q->statusBar()->setVisible(this->ShowStatusBarAction->isChecked());
    q->showMaximized();
    qWarning() << "Kiosk mode unlocked for maintenance";
    }

  emit q->kioskModeChanged(enable);
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

//-----------------------------------------------------------------------------
bool qAksaratorAppMainWindow::isKioskMode() const
{
  Q_D(const qAksaratorAppMainWindow);
  return d->KioskMode;
}

//-----------------------------------------------------------------------------
bool qAksaratorAppMainWindow::isKioskModeRequested()
{
  // Slicer ignores the unknown --kiosk argument, and keeps it when it restarts
  // itself, so a restarted application stays in kiosk mode.
  if (QCoreApplication::arguments().contains(QLatin1String(KioskArgument)))
    {
    return true;
    }
  const QString value = qEnvironmentVariable(KioskEnvironmentVariable).trimmed().toLower();
  return value == QLatin1String("1") || value == QLatin1String("true")
    || value == QLatin1String("yes") || value == QLatin1String("on");
}

//-----------------------------------------------------------------------------
void qAksaratorAppMainWindow::requestKioskUnlock()
{
  Q_D(qAksaratorAppMainWindow);
  if (!d->KioskMode)
    {
    return;
    }

  const QString title = tr("Maintenance mode");
  QSettings settings;
  const QString expectedPinHash =
    settings.value(KioskUnlockPinSha256SettingsKey).toString().trimmed().toLower();
  if (expectedPinHash.isEmpty())
    {
    const QMessageBox::StandardButton answer = QMessageBox::question(this, title,
      tr("Unlock the application for maintenance?\n\nRestart the application to lock it again."));
    if (answer != QMessageBox::Yes)
      {
      return;
      }
    }
  else
    {
    bool accepted = false;
    const QString pin = QInputDialog::getText(this, title, tr("Maintenance PIN:"),
      QLineEdit::Password, QString(), &accepted);
    if (!accepted)
      {
      return;
      }
    const QString pinHash = QString::fromLatin1(
      QCryptographicHash::hash(pin.toUtf8(), QCryptographicHash::Sha256).toHex());
    if (pinHash != expectedPinHash)
      {
      qWarning() << "Kiosk unlock refused: wrong PIN";
      QMessageBox::warning(this, title, tr("Wrong PIN."));
      return;
      }
    }

  d->setKioskMode(false);
}

//-----------------------------------------------------------------------------
void qAksaratorAppMainWindow::closeEvent(QCloseEvent* event)
{
  Q_D(qAksaratorAppMainWindow);
  // Alt+F4, the window manager's close button and File > Exit all end here.
  // An exit the application asks for itself (slicer.app.exit(), restart)
  // does not close the window first, so it still works.
  if (d->KioskMode)
    {
    event->ignore();
    return;
    }
  this->Superclass::closeEvent(event);
}

//-----------------------------------------------------------------------------
void qAksaratorAppMainWindow::showEvent(QShowEvent* event)
{
  Q_D(qAksaratorAppMainWindow);
  // With MainWindow/RestoreGeometry set, the Markups and Sequences modules
  // restore the saved toolbar state when they load, after the window was
  // locked. Hide Slicer's UI again here: Qt has shown the child widgets but
  // has not put the window on screen yet.
  if (d->KioskMode && !event->spontaneous())
    {
    d->hideSlicerChrome();
    }
  this->Superclass::showEvent(event);
}

//-----------------------------------------------------------------------------
void qAksaratorAppMainWindow::changeEvent(QEvent* event)
{
  Q_D(qAksaratorAppMainWindow);
  this->Superclass::changeEvent(event);
  if (event->type() != QEvent::WindowStateChange || !d->KioskMode || !this->isVisible())
    {
    return;
    }
  if (!this->isFullScreen() || this->isMinimized())
    {
    // Something left fullscreen (F11, a window manager key, minimize).
    // Go back on the next event loop turn, not inside the state change.
    QTimer::singleShot(0, this, [this]()
      {
      if (this->isKioskMode() && (!this->isFullScreen() || this->isMinimized()))
        {
        this->showFullScreen();
        }
      });
    }
}

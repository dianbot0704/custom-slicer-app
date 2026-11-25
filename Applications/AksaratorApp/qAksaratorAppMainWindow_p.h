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

#ifndef __qAksaratorAppMainWindow_p_h
#define __qAksaratorAppMainWindow_p_h

// AksaratorApp includes
#include "qAksaratorAppMainWindow.h"

// Qt includes
#include <QDockWidget>
#include <QKeySequence>
#include <QList>
#include <QPair>
#include <QPointer>

// Slicer includes
#include "qSlicerMainWindow_p.h"

class QAction;
class QShortcut;

//-----------------------------------------------------------------------------
class Q_AKSARATOR_APP_EXPORT qAksaratorAppMainWindowPrivate
  : public qSlicerMainWindowPrivate
{
  Q_DECLARE_PUBLIC(qAksaratorAppMainWindow);
public:
  typedef qSlicerMainWindowPrivate Superclass;
  qAksaratorAppMainWindowPrivate(qAksaratorAppMainWindow& object);
  virtual ~qAksaratorAppMainWindowPrivate();

  virtual void init();
  /// Reimplemented for custom behavior
  virtual void setupUi(QMainWindow * mainWindow);

  /// Lock (fullscreen, no Slicer menus/toolbars/shortcuts, no closing) or unlock the window.
  void setKioskMode(bool enable);
  /// Hide Slicer's menu bar, status bar, toolbars and every dock except the module panel.
  void hideSlicerChrome();

  bool KioskMode{false};
  QShortcut* KioskUnlockShortcut{nullptr};
  QList<QPair<QPointer<QAction>, QList<QKeySequence>>> KioskSavedShortcuts;
  QDockWidget::DockWidgetFeatures KioskSavedPanelFeatures;
};

#endif

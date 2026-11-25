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

#ifndef __qAksaratorAppMainWindow_h
#define __qAksaratorAppMainWindow_h

// AksaratorApp includes
#include "qAksaratorAppExport.h"
class qAksaratorAppMainWindowPrivate;

// Slicer includes
#include "qSlicerMainWindow.h"

class Q_AKSARATOR_APP_EXPORT qAksaratorAppMainWindow : public qSlicerMainWindow
{
  Q_OBJECT
  /// True while the window runs locked down as a kiosk (started with
  /// --kiosk or AKSARATOR_KIOSK=1). Scripted modules read it from Python as
  /// slicer.util.mainWindow().kioskMode, and should turn off their own
  /// developer shortcuts while it is true.
  Q_PROPERTY(bool kioskMode READ isKioskMode NOTIFY kioskModeChanged)
public:
  typedef qSlicerMainWindow Superclass;

  qAksaratorAppMainWindow(QWidget *parent=0);
  virtual ~qAksaratorAppMainWindow();

  bool isKioskMode() const;

  /// True if the command line has --kiosk or AKSARATOR_KIOSK is 1/true/yes/on.
  static bool isKioskModeRequested();

public slots:
  void setHomeModuleCurrent() override;
  void on_HelpAboutAksaratorAppAction_triggered();

  /// Ask for confirmation, or for the PIN when Kiosk/UnlockPinSha256 is set,
  /// then unlock the window for maintenance. Restarting the application
  /// locks it again.
  void requestKioskUnlock();

signals:
  void kioskModeChanged(bool kioskMode);

protected:
  qAksaratorAppMainWindow(qAksaratorAppMainWindowPrivate* pimpl, QWidget* parent);

  void closeEvent(QCloseEvent* event) override;
  void showEvent(QShowEvent* event) override;
  void changeEvent(QEvent* event) override;

private:
  Q_DECLARE_PRIVATE(qAksaratorAppMainWindow);
  Q_DISABLE_COPY(qAksaratorAppMainWindow);
};

#endif

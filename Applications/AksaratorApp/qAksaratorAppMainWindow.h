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
public:
  typedef qSlicerMainWindow Superclass;

  qAksaratorAppMainWindow(QWidget *parent=0);
  virtual ~qAksaratorAppMainWindow();

public slots:
  void setHomeModuleCurrent() override;
  void on_HelpAboutAksaratorAppAction_triggered();

protected:
  qAksaratorAppMainWindow(qAksaratorAppMainWindowPrivate* pimpl, QWidget* parent);

private:
  Q_DECLARE_PRIVATE(qAksaratorAppMainWindow);
  Q_DISABLE_COPY(qAksaratorAppMainWindow);
};

#endif

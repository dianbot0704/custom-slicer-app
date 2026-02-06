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

#ifndef __qAIGSlicerAppMainWindow_h
#define __qAIGSlicerAppMainWindow_h

// AIGSlicer includes
#include "qAIGSlicerAppExport.h"
class qAIGSlicerAppMainWindowPrivate;

// Slicer includes
#include "qSlicerMainWindow.h"

class Q_AIGSLICER_APP_EXPORT qAIGSlicerAppMainWindow : public qSlicerMainWindow
{
  Q_OBJECT
public:
  typedef qSlicerMainWindow Superclass;

  qAIGSlicerAppMainWindow(QWidget *parent=0);
  virtual ~qAIGSlicerAppMainWindow();

public slots:
  void setHomeModuleCurrent() override;
  void on_HelpAboutAIGSlicerAppAction_triggered();

protected:
  qAIGSlicerAppMainWindow(qAIGSlicerAppMainWindowPrivate* pimpl, QWidget* parent);

private:
  Q_DECLARE_PRIVATE(qAIGSlicerAppMainWindow);
  Q_DISABLE_COPY(qAIGSlicerAppMainWindow);
};

#endif

/*==============================================================================

  Copyright (c) Kitware, Inc.

  See http://www.slicer.org/copyright/copyright.txt for details.

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  This file was originally developed by Jean-Christophe Fillion-Robin, Kitware, Inc.
  and was partially funded by NIH grant 3P41RR013218-12S1

==============================================================================*/

// AIGSlicer includes
#include "qAIGSlicerAppMainWindow.h"
#include "Widgets/qAppStyle.h"

// Qt includes
#include <QSettings>

// Slicer includes
#include "qSlicerApplication.h"
#include "qSlicerApplicationHelper.h"
#include "vtkSlicerConfigure.h" // For Slicer_MAIN_PROJECT_APPLICATION_NAME
#include "vtkSlicerVersionConfigure.h" // For Slicer_MAIN_PROJECT_VERSION_FULL

namespace
{

//----------------------------------------------------------------------------
void ensureStartupHomeModule(QSettings& settings)
{
  const QString startupModule = QStringLiteral("IntraopPlanner");
  const QString configuredHomeModule = settings.value("Modules/HomeModule").toString();
  // Migrate existing users from previous default values.
  if (configuredHomeModule.isEmpty()
    || configuredHomeModule.compare(QStringLiteral("Home"), Qt::CaseInsensitive) == 0
    || configuredHomeModule == QStringLiteral("IntraOpPlanner"))
    {
    settings.setValue("Modules/HomeModule", startupModule);
    settings.sync();
    }
}

//----------------------------------------------------------------------------
int SlicerAppMain(int argc, char* argv[])
{
  typedef qAIGSlicerAppMainWindow SlicerMainWindowType;

  qSlicerApplicationHelper::preInitializeApplication(argv[0], new qAppStyle);

  qSlicerApplication app(argc, argv);
  if (app.returnCode() != -1)
    {
    return app.returnCode();
    }

  QSettings userSettings;
  ensureStartupHomeModule(userSettings);
  if (QSettings* settings = app.revisionUserSettings())
    {
    ensureStartupHomeModule(*settings);
    }

  QScopedPointer<SlicerMainWindowType> window;
  QScopedPointer<QSplashScreen> splashScreen;

  qSlicerApplicationHelper::postInitializeApplication<SlicerMainWindowType>(
        app, splashScreen, window);

  if (!window.isNull())
    {
    QString windowTitle = QString("%1 %2").arg(Slicer_MAIN_PROJECT_APPLICATION_DISPLAY_NAME).arg(Slicer_MAIN_PROJECT_VERSION_FULL);
    window->setWindowTitle(windowTitle);
    }

  return app.exec();
}

} // end of anonymous namespace

#include "qSlicerApplicationMainWrapper.cxx"

/************************************************************************/
/***********************************************************************/
/**
*	Description:
*		Get the software version number.
*	Parameters:
*		Null
*	Return Value:
*		py::str
*************************************************************************/
py::str Aim_API_GetLibVersion();
/***********************************************************************/
/**
*	Description:
*		Call this function to initialize the API before calling other functions.
*	Parameters:
*		aimHandle: initialization, the initial value to be assigned NULL, each system uses a AimHandle.
*	Return Value:
*		Null
*************************************************************************/
void* Aim_API_Initial();
/************************************************************************/
/**
*	Description:
*		At the end of the program, call this function to close the API.
*	Parameters:
*		aimHandle:Handle to the current API to be closed.
*	Return Value:
*		Null
*************************************************************************/
E_ReturnValue Aim_API_Close(AimHandle &aimHandle);
/************************************************************************/
/**
*	Description:
*		Connect the device using the selected interface, each interface can be used at the same time.
*	Parameters:
*		interfaceType: Specifies the communication interface selected.
		 o_pospara:  Positioner model categories, image parameters
*	Return Value：
*		AIMOOE_OK: The function was executed successfully.
*		AIMOOE_CONNECT_ERROR : Device connection failed, please make sure the device is working properly.
*		AIMOOE_READ_FAULT : Read device error, please reconnect the device or restart the device and try again.
*		AIMOOE_WRITE_FAULT : Write device error, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please make sure the function is called correctly.
*************************************************************************/
E_ReturnValue Aim_ConnectDevice(AimHandle aimHandle, E_Interface interfaceType, T_AIMPOS_DATAPARA &o_pospara);
/************************************************************************/
/**
*	Description:
*		Set the camera acquisition mode: continuous, single active, single slave.
*		This function is only valid for instruments with firmware version V1.2.0 and above.
*		Before calling this function, make sure that the acquired data set by Aim_SetAcquireData() is DT_NONE, which defaults to DT_NONE after the system is connected.
*		This function is only used under USB and Ethernet communication.
*	Parameters:
*		interfaceType: Specifies the communication interface selected.
*		mode: Acquisition mode selection.
*	Return Value:
*		AIMOOE_OK: The function was executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected, please connect the device first.
*		AIMOOE_READ_FAULT: Read device error, please reconnect the device or restart the device and try again.
*		AIMOOE_WRITE_FAULT: Write device error, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please make sure the function is called correctly.
*  Caution:
*   1. The power-on default is continuous acquisition mode. This function does not belong to the memory type parameter setting function, and its set value will not be saved in the camera.
*		Therefore, the factory settings are automatically restored after restarting the instrument.
*   2.When selecting the single acquisition mode, you need to select the corresponding master-slave mode according to different machines.
*	3. Before calling this function, make sure that the acquired data set by Aim_SetAcquireData() is DT_NONE, which defaults to DT_NONE after system connection.
*	4. This function cannot be used under wifi mode.
*************************************************************************/
E_ReturnValue Aim_SetAcquireMode(AimHandle aimHandle, E_Interface interfaceType, E_AcquireMode mode);
/************************************************************************/
/**
*	Description:
*		Obtain marker point coordinates and system status information from the hardware system.
*		This function ensures that the acquired data set by Aim_SetAcquireData() is DT_NONE before it is called, and defaults to DT_NONE after the system is connected.
*	Parameters:
*		interfaceType: Specifies the communication interface selected.
*		markerSt: Stores the returned 3D coordinate information data.
*		statusSt: Stores the returned 3D coordinate information data.
*	Return Value:
*		AIMOOE_OK: The function was executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected, please connect the device first.
*		AIMOOE_READ_FAULT: Read device error, please reconnect the device or restart the device and try again.
*		AIMOOE_WRITE_FAULT: Write device error, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please make sure the function is called correctly.
*  Caution:
*      1.This function ensures that the acquired data set by Aim_SetAcquireData() is DT_NONE before it is called, and defaults to DT_NONE after the system is connected.
*************************************************************************/
E_ReturnValue Aim_GetMarkerAndStatusFromHardware(AimHandle aimHandle, E_Interface interfaceType, T_MarkerInfo & markerSt, T_AimPosStatusInfo& statusSt);
/************************************************************************/
/**
*	Description:
*		Obtain marker point coordinates, system status and binocular image information from the hardware system.
*		This function ensures that the acquired data set by Aim_SetAcquireData() is DT_NONE before it is called, and defaults to DT_NONE after the system is connected.
*		This function is only used under USB and Ethernet communication.
*	Parameters:
*		interfaceType: Specifies the communication interface selected.
*		markerSt: Stores the returned 3D coordinate information data.
*		statusSt: Stores returned system status message data.
*		imageL: Refers to the address that stores the left image data, which needs to be defined by the user, and the image size
*		AP-100:1280*720*1，AP-200:1280*1240*1 1 byte per pixel, pixel refresh direction from left to right, top to bottom.
*		imageR: Refers to the address that stores the right image data, which needs to be defined by the user, and the image size

*		AP-100:1280*720*1，AP-200:1280*1240*1 1 byte per pixel, pixel refresh direction from left to right, top to bottom.
*	Return Value:
*		AIMOOE_OK: The function was executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected, please connect the device first.
*		AIMOOE_READ_FAULT: Read device error, please reconnect the device or restart the device and try again.
*		AIMOOE_WRITE_FAULT: Write device error, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please make sure the function is called correctly.
*  Caution:
*      1. Before calling this function, make sure that the acquired data set by Aim_SetAcquireData() is DT_NONE, which defaults to DT_NONE after system connection.
*		2. This function is only valid for USB and Ethernet communication.
*************************************************************************/
py::dict Aim_GetMarkerStatusAndGreyImageFromHardware(AimHandle aimHandle, E_Interface interfaceType,
 T_AIMPOS_DATAPARA mPosDataPara, T_MarkerInfo & markerSt, T_AimPosStatusInfo& statusSt);

/************************************************************************/
/**
*	Description:
*		Acquire intermediate camera color images from hardware systems. 
*		This function ensures that the acquired data set by Aim_SetAcquireData() is DT_NONE before it is called, and defaults to DT_NONE after the system is connected.
*		This function is only used under USB and Ethernet communication. 
*	Parameters:
*		interfaceType: Specifies the communication interface selected. 
*		o_pospara:  Model category of AimPosition, image parameters
*	Return Value:
*       numpy.array
*       imageC: Refers to the address where the color image data is stored. The image size needs to be defined by the user.
*		1280*720*2，2 bytes per pixel (RGB565, low in front, high in back, high to low)
*		( R->G->B), the pixel refresh direction is from left to right, top to bottom.
* Caution:
*      1.Before calling the function, make sure the data set by Aim_SetAcquireData() is DT_NONE. After connecting the default is DT_NONE
*		2.This function is only valid under USB and Ethernet communication.
*************************************************************************/
numpy.array Aim_GetColorImageFromHardware(AimHandle aimHandle, E_Interface interfaceType, T_AIMPOS_DATAPARA mPosDataPara);
/************************************************************************/
/**
*	Description:
*		Set the data obtained from the camera by the API internal thread. This function must be called before calling the following get function:
*		Aim_GetMarkerInfo()
*		Aim_GetStatusInfo()
*		Aim_GetGreyImageDual()
*		Aim_GetColorImageMiddle()
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		dataType: Make sure the API reads data from the specified communication interface.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*   Caution:
*      1.This function is valid for a long time after called. When reconnecting a read/write error occurs, it should be called again.
*      2.Make sure that the data acquired by the camera contains the data read, otherwise the Get function will return the result of AIMOOE_NOT_REFLASH.
*      3.This function does not belong to the memory parameter setting function. The value set by this function will not be saved in the camera. After restarting the instrument, the default value DT_NONE will be automatically restored.
*************************************************************************/
 E_ReturnValue Aim_SetAcquireData(AimHandle aimHandle, E_Interface interfaceType, E_DataType dataType);
/************************************************************************/
/**
*		Description:
*		Read the latest left and right camera grayscale images from the API internal storage space.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		o_pospara:  Model category of AimPosition, image parameters
*	Return Value:
*       1. The image is stored in " py::dict " dictionary type, the indexes are " dict["imageL"]  "and" dict["imageR"] " respectively, and the dictionary that fails to be called is empty
*		imageL: Points to the address where the left image data is stored. The user needs to define the image size.
*		AP-200:1280*1240*1 Each pixel is 1 byte, and the pixel refresh direction is from left to right and from top down.
*		imageR: Points to the address where the right image data is stored. The user needs to define the image size.
*		AP-200:1280*1240*1 Each pixel is 1 byte, and the pixel refresh direction is from left to right and from top down.
*************************************************************************/
 E_ReturnValue Aim_GetGreyImageDual(AimHandle aimHandle, E_Interface interfaceType,T_AIMPOS_DATAPARA mPosDataPara);
/************************************************************************/
/**
*		Description:
*		Read the latest intermediate camera color image from the API internal storage.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		o_pospara:   Model category of AimPosition, image parameters
*	Return Value:
*       numpy.array
*       imageC: Points to the address where the color image data is stored. The image size needs to be defined by the user.
*		1280*720*2，Each pixel has 2 bytes (RGB565, low bit first, high bit last, from high to low
*		为R->G->B），The pixel refresh direction is from left to right and from top down
*************************************************************************/
 E_ReturnValue Aim_GetColorImageMiddle(AimHandle aimHandle, E_Interface interfaceType, T_AIMPOS_DATAPARA mPosDataPara);
/************************************************************************/
/**
*	Description:
*		Read the latest 3D coordinate information of the marker from the API internal storage space.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		markerSt: Store the returned 3D coordinate information data.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_READ_FAULT: Error reading device. Please reconnect or restart the device and try again.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_NOT_REFLASH: The coordinate information is not updated. At this time, the number of 3D points in markerSt is 0. Please confirm that the data to be acquired by the camera has been correctly set through the Aim_SetAcquireData() function.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*   Caution:
*      After connecting to the system, please call Aim_SetAcquireData() function first, and then call this function.
*************************************************************************/
 E_ReturnValue Aim_GetMarkerInfo(AimHandle aimHandle, E_Interface interfaceType, T_MarkerInfo & markerSt);
/************************************************************************/
/**
*	Description:
*		Set the maximum permissible deviation of point error for tool recognition in mm.
*	Parameters:
*		offset: Maximum permissible deviation of the point error when recognizing the tool, range: 0.3-3.0.
*   Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*      1.This function does not belong to the memory type parameter setting function, its set value will not be saved in the positioner, and the default value of 1.5 will be restored automatically after restarting the instrument.
*************************************************************************/
 E_ReturnValue Aim_SetToolFindOffset(AimHandle aimHandle, float offset = 1.5f);
/************************************************************************/
/**
*	Description:
*		Get the maximum permissible deviation of the point error of the current tool recognition, in mm.
*	Parameters:
*		Null
*   Return Value:
*		offset: Returns the current maximum allowable deviation, range: 0.3-3.0.
*************************************************************************/
 float Aim_GetToolFindOffset(AimHandle aimHandle);
/************************************************************************/
/**
*	Description:
*		Set whether or not point matching error optimization is activated when the tool is recognized, it is activated by default.
*		At startup, an error judgment is made on the matched points, and when the error of a point is larger than that of other points, the point is automatically filtered out when the RT matrix is calculated. 
*	Parameters:
*		en: true to start, false to not start.
*   Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*      1.This function does not belong to the memory type parameter setting function, and its set value will not be saved in the positioner, and the default value will be restored automatically after restarting the instrument. 
*************************************************************************/
 E_ReturnValue Aim_SetToolFindPointMatchOptimizeEnable(AimHandle aimHandle,  bool en= true);
/************************************************************************/
/**
*	Description:
*		Whether or not point matching error optimization is initiated when obtaining the current tool identification.
*		At startup, an error judgment is made on the matched points, and when the error of a point is larger than that of other points,This point is automatically filtered out when calculating the RT matrix.
*Parameters:
*		Null
*  Return Value:
*		true for startup, false for no startup.
*************************************************************************/
 bool Aim_GetToolFindPointMatchOptimizeEnable(AimHandle aimHandle);

/************************************************************************/
/**
*	Description:
*		Reads and checks if the tool file data is correct, the read data is stored in toolData. 
*	Parameters:
*		filePathFullName: Tool file path + name + suffix. 
*		toolData：Returns the tool file data read.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: The tool file is incorrect. 
*************************************************************************/
 E_ReturnValue Aim_CheckToolFile(AimHandle aimHandle, char * filePathFullName, T_ToolFileData &toolData);

/************************************************************************/
/**
*	Description:
*		Set the path of the tool file, the system will traverse the information of all tool files under this path. 
*		When this function is called, the original tool file information is automatically cleared first. 
*		This function does not need to be called multiple times. It is recommended to call this function once after calling the Aim_ConnectDevice() connection function. 
*	Parameters:
*		path: Path parameters. 
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: The path is empty or there is no tool file under the path. 
*   Caution:
*		When calling this function, do not call tool-related functions (e.g., tool lookup functions) in other threads, as this may cause the code to crash! 
*************************************************************************/
 E_ReturnValue Aim_SetToolInfoFilePath(AimHandle aimHandle, char * path);
/************************************************************************/
/**
*	Description:
*		Gets the path to the currently set tool file. 
*	Return Value:
*		const char * path parameter
*************************************************************************/
 const char * Aim_GetToolInfoFilePath(AimHandle aimHandle);
/**
*	Description:
*		Recognizes the Parameters:Marker points in the selected tool file and the coordinates in the tool file by their IDs.
*	Parameters:
*		ptoolid: Tool identification number. 
*		marksize: The number of marker points in the tool file. 
*		toolsysinfo:Marker point datasets in tool files
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_GetSpecificToolFileInfoList(AimHandle aimHandle, const char *ptoolid, int &marksize, std::list<float>*toolsysinfo);
/************************************************************************/
/**
*	Description:
*		Recognizes the Parameters:Marker points in the selected tool file and the coordinates in the tool file by their IDs.
*	Parameters:
*		ptoolid: Tool identification number. 
*		marksize: The number of marker points in the tool file. 
*		toolsysinfo:Marker point datasets in tool files
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_GetSpecificToolFileInfoArray(AimHandle aimHandle, const char* ptoolid, int& markersize, float* toolsysinfo);
/************************************************************************/
/**
*	Description:
*		Gets the number of tool files under the selected path. 
*	Parameters:
*		NULL
*	Return Value:
*		size: Quantity.
*************************************************************************/
 int Aim_GetCountOfToolInfo(AimHandle aimHandle);
/************************************************************************/
/**
*	Description:
*		Get the basic information of all the tool files under the selected path, you can first call the Aim_GetCountOfToolInfo() function to get the number of tool files and initialize the parameter array.
*	Parameters:
*		ptools: Returns an array of structures with basic information about the tool, including name, type and number of markers.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_GetAllToolFilesBaseInfo(AimHandle aimHandle, t_ToolBaseInfo *ptools);

 /************************************************************************/
/**
*	Description:
*		Get the basic information of all the tool files under the selected path, you can first call the Aim_GetCountOfToolInfo() function to get the number of tool files and initialize the parameter array.
*	Parameters:
*		size: 工具数量。
*	返回值：
*		返回工具基本信息的py::dict字典，字典中包括名称，类型 和标记点数量。
*       dict["name"] = 字符串类型
*       dict["isBoard"] = char类型 0是追踪工具 1是注册板工具
*       dict["markcnt"] = int类型
*************************************************************************/
 py::list Aim_GetAllToolFilesBaseInfo(AimHandle aimHandle, int size);

/************************************************************************/
/**
*	Description:
*		All tools under the selected path are recognized by inputting 3D data. 
*		Prior to each call to this function, you can pass Aim_GetMarkerInfo() or the
*		Aim_GetMarkerAndStatusFromHardware()function to get the latest 3D data information. 
*		It is recommended to use Aim_FindSpecificToolInfo() instead of this function, which returns more comprehensive data
*	Parameters:
*		marker: Three-dimensional data. 
*		pResultList: Returns the data that holds the information about the found tool. 
*		minimumMatchPts:The minimum number of match points (≥3) that can be allowed when the multipoint tool is performing recognition. The default value of 0 indicates a full match. 
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Failure to recognize tools.。
*************************************************************************/
 E_ReturnValue Aim_FindToolInfo(AimHandle aimHandle, T_MarkerInfo & marker, T_AimToolDataResult*pResultList, int minimumMatchPts =0);
/************************************************************************/
/**
*	Description:
*		By inputting 3D data and tool ID information (can be more than one), the corresponding tool (can be more than one) is recognized. 
*		Before each call to this function, it can be passed through Aim_GetMarkerInfo() or Aim_GetMarkerAndStatusFromHardware()
*		function to get the latest 3D data information. 
*	Parameters:
*		marker: 3D data list
*		toolids:list of IDs recognized by the tool
*		pResultList: Returns the dataset that holds the found tool information. 
*		minimumMatchPts:The minimum number of match points (≥3) that can be allowed when the multipoint tool is performing recognition.The default value of 0 indicates a full match.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Failure to recognize tools.
*************************************************************************/
 E_ReturnValue Aim_FindSpecificToolInfo(AimHandle aimHandle, T_MarkerInfo & marker,
	const std::vector<std::string>&toolids, T_AimToolDataResult*pResultList, int minimumMatchPts=0);

/************************************************************************/
/**
*	Description:
*		The tool is identified by entering 3D data and ID information for the individual tool.
*		Before each call to this function, it can be passed through Aim_GetMarkerInfo() or Aim_GetMarkerAndStatusFromHardware()
*		function to get the latest 3D data information.
*	Parameters:
*		marker: 3D data list
*		toolids:ID of the tool to be recognized
*		dataResult: Returns the dataset that holds the found tool information. 
*		minimumMatchPts:The minimum number of match points (≥3) that can be allowed when the multipoint tool is performing recognition.The default value of 0 indicates a full match.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Failure to recognize tools.
*************************************************************************/
 E_ReturnValue Aim_FindSingleToolInfo(AimHandle aimHandle, T_MarkerInfo & marker,
	const char * toolids, T_AimToolDataResultSingle &dataResult, int minimumMatchPts = 0);

/************************************************************************/
/**
*	Description:
*		Sets the direction of all coordinate transformation relations (RT matrices, rotation vectors, and quaternions) in the results obtained during tool lookup; the default direction is from the tool coordinate system to the system coordinate system. 
*		The API functions affected by this function setting are:
*		Aim_FindToolInfo()
*		Aim_FindSpecificToolInfo()
*		Aim_FindSingleToolInfo()
*		Aim_MappingPointSetsForMarkerSpaceReg()
*	Parameters:
*		direction: There are two directions, from tools to systems and from systems to tools. 
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Failure to recognize tools.
*************************************************************************/
 E_ReturnValue Aim_SetToolFindRTDirection(AimHandle aimHandle, E_RTDirection direction);

/************************************************************************/
/**
*	Description:
*		Gets the orientation of all coordinate transformation relations (RT matrices, rotation vectors, and quaternions) in the results obtained when the tool looks up. 
*	Parameters:
*		direction: There are two directions, from tools to systems and from systems to tools. 
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Failure to recognize tools.
*************************************************************************/
 E_ReturnValue Aim_GetToolFindRTDirection(AimHandle aimHandle, E_RTDirection &direction);

/************************************************************************/
/**
*	Description:
*		Initialize the information of the tool file to be created based on the tool ID and the number of marker points. 
*		The file is saved under the tool path set by the Aim_SetToolInfoFilePath() function.
*		Therefore, the Aim_SetToolInfoFilePath() function needs to be called before calling this function. 
*	Parameters:
*		markcnt：Number of marking points on the tool
*		id：Tool ID number
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_InitToolMadeInfo(AimHandle aimHandle, const int markcnt, const char * id);
/************************************************************************/
/**
*	Description:
*		Make a tool file and call Aim_InitToolMadeInfo() to initialize the tool information before use. 
*		The tool making process needs to call the and this function to get the coordinates of the marker points in a loop until Proinfo.isMadeProFinished is true.
*	Parameters:
*		marker：Marks the collection of points;
*		ProInfo:  Process information,when Proinfo.isMadeProFinished is true, the production is finished;
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.。
*************************************************************************/
 E_ReturnValue Aim_ProceedToolMade(AimHandle aimHandle, T_MarkerInfo &marker, t_ToolMadeProInfo&ProInfo);
/************************************************************************/
/**
*	Description:
*		Save or cancel the information of the file produced by the tool, and recall it after the production tool is finished.
*	Parameters:
*		saved: true Default saves the tool file information; false deletes the current file information after Aim_DoneToolMade is made;
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_SaveToolMadeRlt(AimHandle aimHandle, bool saved = true);

/************************************************************************/
/**
*	Description:
*		Select the tool to be registered (calibrated) with the tip and the registration board (calibration board) to be used. (It is not recommended to use this function)
*		It is recommended to use Aim_InitToolTipCalibrationWithToolId() instead of this function.
*	Parameters:
*		CalToolIndex Currently selected registration board (calibration board) (index of acquired tool files)
		PosToolIndex Currently selected tool (index of fetched tool files)
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_InitToolTipCalibration(AimHandle aimHandle, int CalToolIndex, int PosToolIndex);
/************************************************************************/
/**
*	Description:
*		Select the tool for which the tip needs to be registered (calibrated) and the registration plate (calibration plate) to be used by the tool ID. 
*	Parameters:
*		CalTool ID number of the currently used registration board (calibration board)
*		PosTool ID number of the currently selected tool
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Function execution failed. 
*************************************************************************/
 E_ReturnValue Aim_InitToolTipCalibrationWithToolId(AimHandle aimHandle, const char* CalTool, const char* PosTool);
/************************************************************************/
/**
*	Description:
*		Operate the selected tool and the registration board (calibration board) to get the tip information of the tool, Before calling, need
*	    Call the Aim_InitToolTipCalibrationWithToolId function to set the selected tool and registration plate (calibration plate). 
*		This function (and the function to get the coordinates of the marker) needs to be called multiple times until info.isCalibrateFinished is true
*	Parameters:
*		marker ：Currently captured marker point
*		ProInfo：Returns the parameters of the tip, the result is valid when the flag bit ProInfo.isCalibrateFinished is true
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Function execution failed.
*************************************************************************/
 E_ReturnValue Aim_ProceedToolTipCalibration(AimHandle aimHandle, T_MarkerInfo & marker, t_ToolTipCalProInfo &ProInfo);
/************************************************************************/
/**
*	Description:
*		Save the registered (calibrated) tool tip information to the original tool file. 
*	Parameters:
*		null
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: fail to save.
*************************************************************************/
 E_ReturnValue Aim_SaveToolTipCalibration(AimHandle aimHandle);

/************************************************************************/
/**
*	Description:
*		Select the registration board (calibration board) to be used and the tool whose coordinates need to be converted by the tool ID. 
*	Parameters:
*		CalTool ID number of the currently used registration board (calibration board)
*		PosTool ID number of the currently selected tool
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Function execution failed.
*************************************************************************/
 E_ReturnValue Aim_InitToolCoordinateRenewWithToolId(AimHandle aimHandle, const char * CalTool, const char * PosTool);
/************************************************************************/
/**
*	Description:
*		Operate the selected tool and the registration plate (calibration plate) to transfer the coordinate system of the tool under the coordinate system of the registration plate. Before calling
*	    The Aim_InitToolCoordinateRenewWithToolId function needs to be called to set the selected registration board (calibration board) and tool.
*		This function (and the function to get the coordinates of the marker) needs to be called multiple times until info.isCalibrateFinished is true
*	Parameters:
*		marker ：Currently captured marker point
*		ProInfo：Returns the parameters of the chipping tool, the result is valid when the flag bit ProInfo.isCalibrateFinished is true.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Function execution failed.
*************************************************************************/
 E_ReturnValue Aim_ProceedToolCoordinateRenew(AimHandle aimHandle, T_MarkerInfo & marker, t_ToolTipCalProInfo & info);
/************************************************************************/
/**
*	Description:
*		Save the coordinates updated tool information to the original tool file. 
*	Parameters:
*		Null
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: fail to save.
*************************************************************************/
 E_ReturnValue Aim_SaveToolCoordinateRenew(AimHandle aimHandle);

/************************************************************************/
/**
*	Description:
*		Select the tool to be registered (calibrated) with the tip by the tool ID, and complete the tip registration by rotating around the point. 
*	Parameters:
*		toolID: ID number of the currently selected tool
*		clearTipMid: When true, the data at the point on the tip is cleared to 0; when false, the data at the point on the tip remains unchanged. 
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Function execution failed.
*************************************************************************/
 E_ReturnValue Aim_InitToolTipPivotWithToolId(AimHandle aimHandle, const char* toolID, bool clearTipMid=false);
/************************************************************************/
/**
*	Description:
*		Data collection was performed on the selected tool to get the tip information of the tool, before calling function, need
*	    Call the Aim_InitToolTipPivotWithToolId function to set the selected tool. 
*		This function (and the function to get the coordinates of the marker) needs to be called multiple times until info.isCalibrateFinished is true.
*		Please start rotating the tip of the needle to be registered around the point beforehand, and then use this function. 
*	Parameters:
*		marker ：Currently captured marker point
*		pivotInfo：Returns the parameters of the needle tip, the result is valid when the flag bit ProInfo.isCalibrateFinished is true.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Function execution failed.
*************************************************************************/
 E_ReturnValue Aim_ProceedToolTipPivot(AimHandle aimHandle, T_MarkerInfo & marker, T_ToolTipPivotInfo &pivotInfo);
/************************************************************************/
/**
*	Description:
*		Save the registered (calibrated) tool tip information to the original tool file. 
*	Parameters:
*		Null
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: fail to save.
*************************************************************************/
 E_ReturnValue Aim_SaveToolTipPivot(AimHandle aimHandle);

/************************************************************************/
/**
*	Description:
*		Select the tool to be calibrated and call it before calling Aim_ProceedToolSelfCalibration
*		Calling this function is not recommended;
*		It is recommended to use Aim_InitToolSelfCalibrationWithToolId() instead of this function.
*	Parameters:
*		ToolIndex Currently selected tool (index of fetched tool files)
*		markcnt  Returns the number of marker points for the selected tool
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Function execution failed.
*************************************************************************/
 E_ReturnValue Aim_InitToolSelfCalibration(AimHandle aimHandle, int ToolIndex, int &markcnt);
/************************************************************************/
/**
*	Description:
*		Select the tool to be calibrated before calling Aim_ProceedToolSelfCalibration
*	Parameters:
*		tool ID number of the currently selected tool
*		
*	Return Value:
*		int Returns the number of marker points for the selected tool Return Value -1 is failed
*************************************************************************/
int Aim_InitToolSelfCalibrationWithToolId(AimHandle aimHandle, const char* tool);
/************************************************************************/
/**
*	Description:
*		To perform a self-calibration operation on the selected tool, you need to call Aim_InitToolSelfCalibrationWithToolId 
*	to set the selected tool before calling it.This function needs to be called several times until the isCalibrateFinished parameter in ProInfo is true.
*	Confirm that the accuracy meets the requirements and save the result according to other parameters in ProInfo. 
*	Parameters:
*		marker: Currently captured marker point
*		ProInfo: Returns the calibration result, where the ProInfo.isCalibrateFinished parameter is true, indicating that the calibration operation is complete. 
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: The function execution fails and the current calibration is invalidated.
*************************************************************************/
 E_ReturnValue Aim_ProceedToolSelfCalibration(AimHandle aimHandle, T_MarkerInfo &marker, t_ToolFixProInfo&ProInfo);
/************************************************************************/
/**
*	Description:
*		Operational processing of calibration results for selected tools

*	Parameters:
*		fixrltcmd Cancel, Redo and Save
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the functi
*************************************************************************/
 E_ReturnValue Aim_SaveToolSelfCalibration(AimHandle aimHandle, E_ToolFixRlt fixrltcmd);

/************************************************************************/
/**
*	Description:
*		Read system status information.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		statusSt: Stores the returned system status information data.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_READ_FAULT: Error reading device. Please reconnect or restart the device and try again.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_NOT_REFLASH: If the data to be acquired by the camera has been correctly set by the Aim_SetAcquireData function, the system status information is not updated.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_GetStatusInfo(AimHandle aimHandle, E_Interface interfaceType, T_AimPosStatusInfo & statusSt);
/************************************************************************/
/**
*	Description:
*		Read the camera factory information.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		manufactureInfo: Store the returned factory information data.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_GetManufactureInfo(AimHandle aimHandle, E_Interface interfaceType, T_ManufactureInfo & manufactureInfo);

/************************************************************************/
/**
*	Description:
*		Issue camera system instructions.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		com: The command value to be issued.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_WRITE_FAULT : Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_SetSystemCommand(AimHandle aimHandle, E_Interface interfaceType, E_SystemCommand com);

/************************************************************************/
/**
*	Description:
*		Set the exposure value of the left and right cameras (the last set value is used by default when the camera is turned on). Range:
*		16-16384 (ie: 0x10-0x4000), unit is us, the minimum resolution is 16us.
*		The setting of this exposure value will affect the acquisition accuracy, please do not modify it at will.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		expTime: The exposure value of the binocular left and right cameras to be set, range: 16-16384 (ie: 0x10-0x4000),
*		The unit is us, and the minimum resolution is 16us.

*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*		1. This function belongs to the memory parameter setting function. The set value will be saved in the camera and will be restored the next time it is opened.
*		It will be used when locating the instrument.
*		2.Since the memory parameter setting function needs to wait for the camera to save the data, after this function is called,
*		A delay of more than 0.5s is required before calling the next memory parameter setting function.
*************************************************************************/
 E_ReturnValue Aim_SetDualExpTime(AimHandle aimHandle, E_Interface interfaceType, int expTime);

/************************************************************************/
/**
*	Description:
*		Set the exposure value of the binocular camera according to the use distance.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		distanceInMM: Use distance, in millimeters
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*		1.This function belongs to the memory parameter setting function. The set value will be saved in the camera and will be restored
*		The settings will be used next time you turn on the camera.
*		2.Since the memory parameter setting function needs to wait for the camera to save the data, after this function is called,
*		A delay of more than 0.5s is required before calling the next memory parameter setting function.
*************************************************************************/
 E_ReturnValue Aim_SetDualExpTimeByDistance(AimHandle aimHandle, E_Interface interfaceType, int distanceInMM);

/************************************************************************/
/**
*	Description:
*		Set the delay between the flash and the exposure time. Including start delay and shut down delay.
*		When using the API normally, there is no need to modify the delay parameters.
*		This function is only used in USB and Ethernet communication.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		flashOnDelay: Delay time from flash start to camera exposure start = flashOnDelay*125us, value range of flashOnDelay 0-255.
*		flashOffDelay: Delay time from flash off to camera exposure off = flashOffDelay*125us, flashOffDelay value range 0-255.
*								Also, the delay time from flash off to camera exposure off must be less than the exposure time.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*		1.This function does not belong to the memory type parameter setting function, and its set value will not be saved in the positioner, and the default value will be restored automatically after restarting the instrument. 
*		2.This function cannot be used under wifi.
*************************************************************************/
 E_ReturnValue Aim_SetFlashDelay(AimHandle aimHandle, E_Interface interfaceType, int flashOnDelay, int flashOffDelay);

/************************************************************************/
/**
*	Description:
*		Sets the exposure value for the intermediate color camera, range: 48-8192 (i.e.: 0x30-0x2000).
*		This setting will not be effective if the color camera auto exposure is turned on (turned on by default at power on).
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		expTimeAF: Intermediate color camera exposure value to be set, range: 48-8192 (i.e., 0x30-
*		0x2000)，The unit is: transmission time for 1 line of image/16.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*		1.The exposure value set by this function will not be saved in the camera because the power-up default turns on the automatic exposure of the intermediate color camera. 
*************************************************************************/
 E_ReturnValue Aim_SetColorExpTime(AimHandle aimHandle, E_Interface interfaceType, int expTimeAF);

/************************************************************************/
/**
*	Description:
*		Set the collision detection sensitivity, range: 1-10, 1 sensitivity is the highest, 10 sensitivity is the lowest. 
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		level: Sensitivity parameter, the lower the value, the more sensitive. 
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*		1.This function belongs to the memory parameter setting function. The set value will be saved in the camera and will be restored
*		The settings will be used next time you turn on the camera.
*		2.Since the memory parameter setting function needs to wait for the camera to save the data, after this function is called,
*		A delay of more than 0.5s is required before calling the next memory parameter setting function.
*************************************************************************/
 E_ReturnValue Aim_SetCollisinoDetectLevel(AimHandle aimHandle, E_Interface interfaceType, UCHAR level);
/************************************************************************/
/**
*	Description:
*		Set the IP of the camera (factory default is 192.168.31.10), restart the camera after setting is valid. 
*		Currently, only the IP setting of the camera is supported under USB and network port connection. 
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*		IP_A、IP_B、IP_C、IP_D: The four fields A.B.C.D of the IP address to be set, each field
*		Occupies one byte.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*		1.This function belongs to the memory parameter setting function. The set value will be saved in the camera and will be restored
*		The settings will be used next time you turn on the camera.
*		2.Since the memory parameter setting function needs to wait for the camera to save the data, after this function is called,
*		A delay of more than 0.5s is required before calling the next memory parameter setting function.
*		3.This function cannot be used under wifi.
*************************************************************************/
 E_ReturnValue Aim_SetAimPositionIP(AimHandle aimHandle, E_Interface interfaceType, UCHAR IP_A, UCHAR IP_B, UCHAR IP_C, UCHAR IP_D);
/************************************************************************/
/**
*	Description:
*		Get the IP currently used by the camera.
*		Available after successful connection in any way.
*	Parameters:
*		interfaceType: Specifies the communication interface to be used.
*	Return Value:
*		numpy.array type, IP_A、IP_B、IP_C、IP_D: The four fields A.B.C.D of the IP address to be connected, each field
*		Occupies one byte. 
*************************************************************************/
 numpy.array Aim_GetAimPositionIP(AimHandle aimHandle, E_Interface interfaceType);
/************************************************************************/
/**
*	Description:
*		For Ethernet connection, set the IP of the locator to be connected, which needs to be the same as the IP of the locator set.
*	Parameters:
*		IP_A、IP_B、IP_C、IP_D: The four fields A.B.C.D of the IP address to be connected, each field
*		Occupies one byte. 
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*		1.This function needs to be used before the Aim_ConnectDevice() function is called. 
*		2.This function does not need to be called if the camera IP is using the factory default settings (192.168.31.10). 
*************************************************************************/
 E_ReturnValue Aim_SetEthernetConnectIP(AimHandle aimHandle, UCHAR IP_A, UCHAR IP_B, UCHAR IP_C, UCHAR IP_D);
/************************************************************************/
/**
*Description:
*		Gets the currently set IP of the locator to be connected, which is not equal to the IP used by the current locator.
*	Parameters:
*		Null
*	Return Value:
*		numpy.array tyoe,IP_A、IP_B、IP_C、IP_D: The four fields A.B.C.D of the IP address to be connected, each field
*		Occupies one byte. 
*	Caution:
*		1.This IP is not equivalent to the IP currently used by the AimPosition.
*************************************************************************/
numpy.array Aim_GetEthernetConnectIP(AimHandle aimHandle);
/************************************************************************/
/**
*	Description:
*		Sets whether the locator LCD screen displays unprocessed points. 
*		The factory default is not to display unprocessed points, i.e., only points from the left and right cameras that are a match are displayed. 
*		This function is only used in USB and Ethernet communication.
*	Parameters:
*		isRawPointShow: true displays unprocessed points; false displays only processed points.
*   Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*		1.This function belongs to the memory parameter setting function. The set value will be saved in the camera and will be restored
*		The settings will be used next time you turn on the camera.
*		2.Since the memory parameter setting function needs to wait for the camera to save the data, after this function is called,
*		A delay of more than 0.5s is required before calling the next memory parameter setting function.
*		3.This function cannot be used under wifi.
*************************************************************************/
 E_ReturnValue Aim_SetLCDShowRawPoint(AimHandle aimHandle, E_Interface interfaceType, bool  isRawPointShow = false);

/************************************************************************/
/**
*	Description:
*		Sets the parameter threshold for marker point recognition, which is generally not recommended to be modified.
*		This function is only used in USB and Ethernet communication.
*	Parameters:
*		minRoundness: Roundness threshold, range: 0-100;
*		maxArea: Area threshold, range: 5-4000;
*		minBrightness: Brightness threshold, range: 1-255;
*   Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_WRITE_FAULT: Error writing to device, please reconnect the device or restart the device and try again.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:
*		1.This function is not a memory type parameter setting function and the value it sets will not be saved in the camera.
*		Therefore, the factory settings are automatically restored after restarting the instrument. 
*		2.This function cannot be used under wifi.
*************************************************************************/
 E_ReturnValue Aim_SetMarkerParameters(AimHandle aimHandle, E_Interface interfaceType, int minRoundness=75, int maxRoundness = 100, int minArea = 5, int maxArea = 1000, int minBrightness = 80);
/************************************************************************/
/**
*	Description:
*		Initialize the ID number of the accuracy test tool used, only the left and right four-point aimooe accuracy tools are supported
*	Parameters:
*		toolids:ID numbers for all points of the tool, toolidl left 4-point tool ID, toolid2 right 4-point tool ID
*	Return Value:
*		AIMOOE_OK: The function executes successfully, indicating that an accuracy test can be performed.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.		
*************************************************************************/
 E_ReturnValue Aim_InitAccuracyCheckTool(AimHandle aimHandle, const char *toolids, const char*toolid1, const char*toolid2);
/************************************************************************/
/**
*	Description:
*		Call this function (and the function to get the coordinates of the marker points) in a loop as needed. 
*	Parameters:
*		markarr:markerset[markcnt][3]
*		markcnt:Number of marker points
*		T_AccuracyToolResult:Distance and rotation angle of the left and right tools for the current acquisition
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*   Caution:
*	After this function is called, the data is stored internally for the Aim_AccuracyCheckToolCalculateError function to perform calculations
*************************************************************************/
 E_ReturnValue Aim_AccuracyCheckTool(AimHandle aimHandle, py::array_t<double> markarr, const int markcnt, T_AccuracyToolResult& Rlt);
/************************************************************************/
/**
*	Description:
*		Obtain positioning system accuracy error data, including mean, standard deviation, and angular error.
*	Parameters:
*		meanerro Mean error, stdev distance standard deviation, angle[3] angle mean error. 
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*	 Caution:This function is called to zero out the internally stored data. 
*************************************************************************/
 py::tuple Aim_AccuracyCheckToolCalculateError(AimHandle aimHandle);
/************************************************************************/
/**
*	Description:
*		Point set initialization for spatial alignment, passing spatial point set information as a tool to the optical positioning system
*	Parameters:
*		ImgPtArr Image space coordinate point set
*		ImgPtSize Number of point sets
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_InitMappingPointSetsForMarkerSpaceReg(AimHandle aimHandle, py::array_t<float> ImgPtArr, const int ImgPtSize);
/************************************************************************/
/**
*	Description:
*		Spatial point set alignment, obtaining relevant information after alignment
*	Parameters:
*		marker：Three-dimensional point set acquired by an optical positioning system
*		pResultList：Results after registration
*		minimumMatchPts:The minimum number of match points (≥3) that can be allowed when the multipoint tool is performing recognition.The default value of 0 indicates a full match.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_MappingPointSetsForMarkerSpaceReg(AimHandle aimHandle, T_MarkerInfo & marker, T_AimToolDataResult * pResultList, int minimumMatchPts=0);

/************************************************************************/
/**
*		Description:
*		Setting up calibration results and tracked results for robot control
*	Parameters:
*		Sys2RobotBaseRTArray RT array from optical localization system to robot base (3*4 array, columns 0-2 R, column 3 dimension T)
* 	    Tool2RobotEndRTArray RT array from tool to robot end (3*4 array, columns 0-2 are R, column 3 is dimension T)
*		toolid Tool ID number		
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_SetRobotCalculateRlt(AimHandle aimHandle, py::array_t<double> Sys2RobotBaseRTArray, py::array_t<double> Tool2RobotEndRTArray, const char* toolid);
/************************************************************************/
/**
*	Description:
*		Calculate the target position of the robot path
*	Parameters:
*		TargetPathArr Paths under optical localization system: array of format 2*3, 0*3 for safe points, 1*3 for target points (XYZ)
* 	    targetPoseArr Target Position Array[X,Y,Z,Rx,Ry,Rz]

*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_CalculateRobotTargetPose(AimHandle aimHandle, py::array_t<double> TargetPathArr, py::array_t<float> targetPoseArr);

/************************************************************************/
/**
*	Description:
*		Get device MAC address (format: hexadecimal xx:xx:xx:xx:xx:xx)
*	Parameters:
*		Null
*	Return Value:
*		numpy.array type ,addr：Mac address of the current device
*************************************************************************/
numpy.array Aim_GetAimPositonMacAddress(AimHandle aimHandle);

/************************************************************************/
/**
*	Description:
*		Calculate 3D point coordinates from 2D point coordinates. 
*	Parameters:
*		leftPoint: Array of 2D point coordinates (x, y) for the left image, up to 200. 
*		leftNum：Left image 2D point count, up to 200. 
*		rightPoint: Array of 2D point coordinates (x, y) for the right image, up to 200. 
*		rightNum：Right image 2D point count, up to 200. 
*		markerSt: Store the returned 3D coordinate information data.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_NOT_CONNECT: The device is not connected. Please connect the device first.
*		AIMOOE_ERROR: Unknown error, please confirm that the function call is correct.
*************************************************************************/
 E_ReturnValue Aim_Calculate3DPoints(AimHandle aimHandle, float leftPoint[400], int leftNum, float rightPoint[400], int rightNum, T_MarkerInfo & markerSt);

/************************************************************************/
/**
*	Description:
*		Select the registration board (calibration board) to be used and the tool whose coordinates need to be converted by the tool ID. 
*	Parameters:
*		CalTool ID number of the currently used registration board (calibration board)
*		PosTool ID number of the currently selected tool
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Function execution failed.
*************************************************************************/
E_ReturnValue Aim_InitToolCoordinateRenewWithToolId(AimHandle aimHandle, const char * CalTool, const char * PosTool);
/************************************************************************/
/**
*	Description:
*		Operate the selected tool and the registration plate (calibration plate) to transfer the coordinate system of the tool under the coordinate system of the registration plate. Before calling
*	    The Aim_InitToolCoordinateRenewWithToolId function needs to be called to set the selected registration board (calibration board) and tool.
*		This function (and the function to get the coordinates of the marker) needs to be called multiple times until info.isCalibrateFinished is true
*	Parameters:
*		marker ：Currently captured marker point
*		ProInfo：Returns the parameters of the chipping tool, the result is valid when the flag bit ProInfo.isCalibrateFinished is true.
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: Function execution failed.
*************************************************************************/
E_ReturnValue Aim_ProceedToolCoordinateRenew(AimHandle aimHandle, T_MarkerInfo & marker, t_ToolTipCalProInfo & info);
/************************************************************************/
/**
*	Description:
*		Save the coordinates updated tool information to the original tool file. 
*	Parameters:
*		Null
*	Return Value:
*		AIMOOE_OK:The function executed successfully.
*		AIMOOE_ERROR: fail to save.
*************************************************************************/
E_ReturnValue Aim_SaveToolCoordinateRenew(AimHandle aimHandle);

/************************************************************************/
/**
*	Description:
*		The function is the same as that of the Aim_FindSpecificToolInfo function, but the return result is different, 
*		and the return is a map, the key is the tool name, and the value is the tool information.
*	Parameter:
*		marker: The current collection of markers
*		toolids: a list of tool names that currently need to be converted
*		resultMap: Tool information
*		minimumMatchPts: The minimum number of match points
*	Return value:
*		AIMOOE_OK: The function is executed successfully.
*		AIMOOE_ERROR: Execution failed
*************************************************************************/
E_ReturnValue Aim_FindToolInfo_Map(AimHandle aimHandle, T_MarkerInfo& marker,
	std::vector<std::string>& toolids, std::map<std::string, T_AimToolDataResult*>& resultMap, int minimumMatchPts = 0);
/************************************************************************/
/**
*	Description:
*		Set the tool existing in the tool folder as a reference tool, if the tool folder does not have the tool, it will return the AIMOOE_ERROR, 
*		and after setting, the Aim_GetToolInfoInRef function will return the information in the coordinate system of the tool, and only one tool can be set.
*Parameter:
*		referTool: Refer to the name of the tool, no suffix is required
*	Return value:
*		AIMOOE_OK: The function is executed successfully
*		AIMOOE_ERROR: Execution failed
*************************************************************************/
E_ReturnValue Aim_SetReferenceTool(AimHandle aimHandle,	const char* referTool);
/************************************************************************/
/**
*	Description:
*		To use it in pairs with Aim_SetReferenceTool, you need to call the Aim_SetReferenceTool function to set up the reference tool first, and call it directly will return the AIMOOE_ERROR
*		 The result will be stored in the resultMap, the key is the tool name, and the value is the tool information
*	Parameter:
*		marker: The current collection of markers
*		toolids: a list of tool names that currently need to be converted
*		resultMap: Tool information
*		minimumMatchPts: The minimum number of match points
*	Return value:
*		AIMOOE_OK: The function is executed successfully.
*		AIMOOE_ERROR: Execution failed
*************************************************************************/
E_ReturnValue Aim_GetToolInfoInRef(AimHandle aimHandle, T_MarkerInfo& marker,
	std::vector<std::string>& toolids, std::map<std::string, T_AimToolDataResult*>& resultMap, int minimumMatchPts = 0);
/************************************************************************/
/**
*	Description:
*		Cancels the reference coordinate system conversion state and clears the tools Aim_SetReferenceTool settings
*Parameter:
*		Null
* Return value:
*		AIMOOE_OK: The function is executed successfully.
*		AIMOOE_ERROR: Execution failed
*************************************************************************/
E_ReturnValue Aim_CancelRef(AimHandle aimHandle);

/************************************************************************/
/**
*	Description:
*		Compatible with NDI tools, convert files ending in.rom suffixes to.aimtool files
* Parameter :
*		NDIFilename : the name of the NDI tool file
* Return value :
*		AIMOOE_OK : The function is executed successfully.
*		AIMOOE_ERROR : Execution failed
*************************************************************************/
E_ReturnValue Aim_ConvertNDIrom2Aimtool(AimHandle aimHandle, const char* NDIFilename);







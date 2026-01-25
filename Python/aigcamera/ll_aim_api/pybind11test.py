# -*- coding: utf-8 -*-
"""
Created on Thu Mar 13 16:59:40 2025

@author: Aimooe
"""

import AimPosition as ap
import time
from PIL import Image
import numpy as np

def caseTitle():
    print("Please enter the instruction number (01-99) and press enter:")
    print("01.Turn on the laser projector")
    print("02. Turn off the laser projector")
    print("03. Turn on IR illumination ring")
    print("04. Turn off the IR illumination ring")
    print("05.Turn on Clash Detection")
    print("06.Turn off clash detection")
    print("07.Clear Collision Flag")
    print("08. Set the collision detection sensitivity to 1 (most sensitive)")
    print("09. Set the collision detection sensitivity to 10 (least sensitive)")
    
    print("10. Set the data acquired from the AimPosition to be empty")
    print("11.Set the data obtained from the AimPosition as information data (including system status and 3D coordinates)")
    # if EI != ap.E_ReturnValue.I_WIFI:
    #   print("12.Set the data acquired from the AimPosition to binocular grayscale image data")
    #   print("13.Set the data acquired from the AimPosition to intermediate color image data")
    #   print("14.Set the data acquired from the AimPosition as information data and binocular grayscale image data")
    #   print("15.Set the data acquired from the AimPosition as information data and intermediate color image data")
    #   print("16. Set the data acquired from the AimPosition as information data, binocular grayscale image data, and intermediate color image data")
    # else
    #   print("17.Set the data acquired from the AimPosition as 3D coordinate data")
    #   print("18.Set the data acquired from the AimPosition as system status data")
    
    print("20. Turn off the touch display")
    print("21.Turn on the touch display")
    print("22.Reset the touch display")
    print("23.Switch touch screen page to: Marker Point Detection page")
    print("25.Switch touch screen page to: middle color image page")
    print("26.Set the points displayed on the touchscreen marker point detection page to be unprocessed")
    print("27.Set the points displayed on the touchscreen marker point detection screen to the processed points")
    
    print("30. Start middle camera AE")
    print("31. Turn off middle camera AE")
    print("32. Set the intermediate camera exposure value to 4000")
    print("33.Start the middle camera and keep focusing")
    print("34. Turn off the middle camera and keep focusing")
    print("35.Start the middle camera one-shot focus")
    print("36.Intermediate camera fixed focal length to infinity")
    
    print("40.Enable binocular AE (off by default when powered on)")
    print("41.Turn off binocular AE (off by default)")
    print("42.Set the exposure value of the binocular camera (1000 on the left and right)")
    print("43.Set the exposure value at the distance from the Z-axis value of the acquired marker point (median value when there are multiple points)")
    print("44. Set flash delay")
    
    print("50.Get System Status Information")
    print("51.Get 3D coordinate information of marker points")
    # if EI != ap.E_ReturnValue.I_WIFI:
    #   print("52. Get left and right camera images Left.bmp and Right.bmp to the CameraImage folder)
    #   print("53. Get intermediate color camera images Color.bmp to the CameraImage folder")
    print("54.Get the current IP address information")
    print("55.Get Factory Information")
    print("56.Get Device Mac Address")
    
    print("60.Get the location tool file under a certain path and get the information of the tool")
    print("61.Get specific information about a particular tool (in the form of a linked list)")
    print("62.Spatial Registration")
    print("63.Make a 4-Point Tool")
    print("64.calibration tool")
    print("65.Tool tip registration (registration board)")
    print("75.Tool tip registration (rotation around the point)")
    print("76.Tool Registration - Coordinate Conversion Version (Transfer the point coordinates of the tool file to the coordinate system of the registered version of the tool file.)")
    
    print("66.AAK Precision Tool Test")
    print("67.Check Tool Files")
    
    print("98.Reselect the connection method")
    #print("99.Exit")

def whichcase(value):
    
    if value == 1:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_LASER_ON)
    elif value == 2:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_LASER_OFF)
    elif value == 3:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_IRLED_ON)
    elif value == 4:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_IRLED_OFF)
    elif value == 5:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_COLLISION_ENABLE)
    elif value == 6:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_COLLISION_DISABLE)
    elif value == 7:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_COLLISION_INFO_CLEAR)
    elif value == 8:
        r=ap.Aim_SetCollisinoDetectLevel(aimHandle,interfaceType,1)
    elif value == 9:
        r=ap.Aim_SetCollisinoDetectLevel(aimHandle,interfaceType,10)
    elif value == 10:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_NONE)
    elif value == 11:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_INFO)
    elif value == 12:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_IMGDUAL)
    elif value == 13:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_IMGCOLOR)
    elif value == 14:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_INFO_IMGDUAL)
    elif value == 15:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_INFO_IMGCOLOR)
    elif value == 16:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_INFO_IMGDUAL_IMGCOLOR)
    elif value == 17:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_MARKER_INFO_WITH_WIFI)
    elif value == 18:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_STATUS_INFO)
    
    elif value == 20:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_LCD_OFF)
    elif value == 21:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_LCD_ON)
        
    elif value == 23:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_LCD_PAGE_SUBPIXEL)
        
    elif value == 25:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_LCD_PAGE_COLOR)
    elif value == 26:
        r=ap.Aim_SetLCDShowRawPoint(aimHandle,interfaceType,True)
    elif value == 27:
        r=ap.Aim_SetLCDShowRawPoint(aimHandle,interfaceType,False)
        
    elif value == 30:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_AF_EXP_AUTO_ON)
    elif value == 31:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_AF_EXP_AUTO_OFF)    
    elif value == 32:
        r=ap.Aim_SetColorExpTime(aimHandle,interfaceType,4000)
    elif value == 33:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_AF_CONTINUOUSLY_ON)    
    elif value == 34:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_AF_CONTINUOUSLY_OFF)    
    elif value == 35:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_AF_SINGLE)    
    elif value == 36:
        r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_AF_FIX_INFINITY)     

    # elif value == 40:
    #  r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_DUALCAM_AUTO_EXP_ON)  
    # elif value == 41:
    #    r=ap.Aim_SetSystemCommand(aimHandle,interfaceType,ap.E_SystemCommand.SC_DUALCAM_AUTO_EXP_OFF)

    elif value == 42:
        r=ap.Aim_SetDualExpTime(aimHandle,interfaceType,1000)
        
    elif value == 43:
        r=ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_NONE)
        if r==ap.E_ReturnValue.AIMOOE_OK:
            r=ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            if r==ap.E_ReturnValue.AIMOOE_OK:
                ZDis = []
                for i in range(markerinfo.MarkerNumber):
                    ZDis.append(markerinfo.MarkerCoordinate[i * 3 + 2])
                
                ZDis.sort(reverse=True)
                mid = len(ZDis) // 2
                dis = ZDis[mid]
                r=ap.Aim_SetDualExpTimeByDistance(aimHandle, interfaceType, dis)
    elif value == 44:
        r=ap.Aim_SetFlashDelay(aimHandle, interfaceType, 1, 0)
        
    elif value == 50:
        r=ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
        if r==ap.E_ReturnValue.AIMOOE_OK:
            print("Current collision status (0: No collision, 1: Collision detected, 2, Detection not enabled):", hardware. CollisionStatus)
            print("CPU Temp (°C):", hardware. Tcpu, " ", "Motherboard Temperature (°C):", hardware. Tpcb)
            print("Is the hardware state OK (1: OK, 0: UNHEALTHY):", hardware. HardwareStatus == ap. E_HardwareStatus.HW_OK)
            print("Frame Rate (Marker Point Sampling) Left Camera:", int(hardware. LeftCamFps), " Right Camera:", int(hardware. RightCamFps),
                  "Color camera:", int(hardware. ColorCamFps), " touchscreen:", int(hardware. LCDFps))
            print("Exposure time left camera:", hardware. ExposureTimeLeftCam, " Right Camera:", hardware. ExposureTimeRightCam)
        elif r==ap. E_ReturnValue.AIMOOE_NOT_REFLASH:
            print("Please confirm that the data you want to retrieve has been set correctly by the Aim_SetAcquireData function and try again")


    elif value == 51:
        while True:
            r=ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            if r==ap.E_ReturnValue.AIMOOE_NOT_REFLASH:
                time.sleep(0.01)
            else:
                break
        if r==ap.E_ReturnValue.AIMOOE_OK:
            markerNum = markerinfo.MarkerNumber
            print(f"{markerinfo.ID} acquisition after booting")
            print(f" marker point background light (1: normal, 0: abnormal): {markerinfo. MarkerBGLightStatus == ap. E_BackgroundLightStatus.BG_LIGHT_OK}")
            print(f"Number of marker points detected: {markerNum}")
            for i in range(markerNum):
                print(f"{i}:({markerinfo.MarkerCoordinate[i * 3 + 0]}, {markerinfo.MarkerCoordinate[i * 3 + 1]}, {markerinfo.MarkerCoordinate[i * 3 + 2]})")
    
            if markerinfo. PhantomMarkerGroupNumber > 0: # Phantom points exist
                # Initialize the storage space of each group of phantom points based on the total number of grouping of phantom points
                PantomMarkerID = [[] for _ in range(markerinfo. PhantomMarkerGroupNumber)]
        
                # Iterate through the phantom point alert array to categorize the phantom points into the corresponding group
                for j in range(markerNum):
                    WarningValue = markerinfo.PhantomMarkerWarning[j]
                    if WarningValue > 0: # indicates that the jth point is a phantom point
                        PantomMarkerID[WarningValue - 1].append(j) # Categorize the point into the corresponding phantom point group    
        
                # Output
                print(f"Possible phantom points share {markerinfo. PhantomMarkerGroupNumber} group. ")
                for j in range(markerinfo. PhantomMarkerGroupNumber):
                    print(f"Dots belonging to group {j + 1}:", end="")
                    for i in PantomMarkerID[j]:
                        print(i, end="  ")
                    print()
            else:
                print("Phantom points are not included in this data")
        elif r==ap. E_ReturnValue.AIMOOE_NOT_REFLASH:
            print("Please make sure that the data you want to retrieve has been set correctly by the Aim_SetAcquireData function and try again!")
    elif value == 52:
        imgDual = ap.Aim_GetMarkerStatusAndGreyImageFromHardware(aimHandle,interfaceType,pospara,markerinfo,hardware)
        if len(imgDual)!=0:
            imgl = np.squeeze(imgDual["imageL"])
            imgl.astype(np.uint8)
            imgr = np.squeeze(imgDual["imageR"])
            imgr.astype(np.uint8)
            #Save the imag
            leftone = Image.fromarray(imgl)
            rightone = Image.fromarray(imgr)

            leftone.show()
            rightone.show()
            leftone.save(str(currentDir/'CameraImage/leftone.png'))
            rightone.save(str(currentDir/'CameraImage/rightone.png'))
            
        else:
            print("Save failed, please confirm that the data you want to get has been set correctly by the Aim_SetAcquireData function and try again!")
    elif value == 53:
        imgColor = ap.Aim_GetColorImageFromHardware(aimHandle,interfaceType,pospara)
        if len(imgColor)!=0:
            imgc = np.squeeze(imgColor)
            imgc = imgc.astype(np.uint8)
            #Save the imag
            colorone = Image.fromarray(imgc)      
            colorone.show()
            colorone.save(str(currentDir/'CameraImage/colorone.png'))
        else:
            print("Save failed, please confirm that the data you want to get has been set correctly by the Aim_SetAcquireData function and try again!")
    
    elif value == 54:
        ipAddr = ap.Aim_GetAimPositionIP(aimHandle,interfaceType)
        if len(ipAddr)!=0:
            print("Current IP:",ipAddr)
        else:
            print("Please connect the AimPosition first!")
            
    elif value == 55:
        r=ap.Aim_GetManufactureInfo(aimHandle,interfaceType,manufactureInfo)
        ver_str = ''.join(manufactureInfo.Version)
        print("Version number",ver_str)
        print("Date of manufacture",manufactureInfo.Year,"/",manufactureInfo.Month,"/",manufactureInfo.Day)
        
    elif value == 56:
        ipMac = ap.Aim_GetAimPositonMacAddress(aimHandle)
        if len(ipMac)!=0:
            ipMac_ascii = [chr(i) for i in ipMac]
            ipMac_str = ''.join(ipMac_ascii)
            print("MAC address:",ipMac_str)
        else:
            print("Unknown error!")
    
    elif value == 60:
        r = ap.Aim_SetToolInfoFilePath(aimHandle,toolPath,True)
        print("tool path:",ap.Aim_GetToolInfoFilePath(aimHandle))
        
        toolSize = ap.Aim_GetCountOfToolInfo(aimHandle)
        print("Number of tools:",toolSize)
        
        if toolSize != 0:
            res = ap.Aim_GetAllToolFilesBaseInfo(aimHandle, toolSize)
            if len(res)!=0:
                for i in range(toolSize):
                    print("Tool name",res[i]['name'])
            else:
                print("There are no tools in the current directory, please check the tool path")
        while True:
            r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            while r == ap.E_ReturnValue.AIMOOE_NOT_REFLASH:
                time.sleep(0.01)
                r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle, interfaceType, markerinfo,hardware)         
                if r != ap.E_ReturnValue.AIMOOE_OK:
                    break
            residualIndex = list(range(markerinfo.MarkerNumber))
            mtoolsrlt = ap.T_AimToolDataResult()
            r = ap.Aim_FindToolInfo(aimHandle,markerinfo,mtoolsrlt,0)
            if r == ap.E_ReturnValue.AIMOOE_OK:
                prlt = mtoolsrlt
                while prlt!=None:
                    if prlt.validflag:
                        PI = 3.1415962
                        print(f"Tool found: {prlt.toolname} Mean error {prlt. MeanError} RMS Error {prlt. Rms}")
                        print(f"tool origin: {prlt. OriginCoor[0]}, {prlt. OriginCoor[1]}, {prlt. OriginCoor[2]}")
                        print(f"tool angle: {prlt.rotationvector[0] * 180 / PI}, {prlt.rotationvector[1] * 180 / PI}, {prlt.rotationvector[2] * 180 / PI}")
                        print("Marker Point Coordinates:")
                        for idx in prlt.toolptidx:
                            if idx in residualIndex:
                                residualIndex.remove(idx)
                            if idx < 0:
                                print("0 0 0")
                            else:
                                print(f"{markerinfo.MarkerCoordinate[idx * 3 + 0]} {markerinfo.MarkerCoordinate[idx * 3 + 1]} {markerinfo.MarkerCoordinate[idx * 3 + 2]}")
                        pnext = prlt.next
                        del prlt
                        prlt = pnext

                if len(residualIndex) > 0:
                    print(f"{len(residualIndex)}discrete points:")
                    for i, j in enumerate(residualIndex):
                        print(f"{i}: {markerinfo.MarkerCoordinate[j * 3 + 0]}, {markerinfo.MarkerCoordinate[j * 3 + 1]}, {markerinfo.MarkerCoordinate[j * 3 + 2]}")
                else:
                    break
            else:
                break
                
        print("End the lookup")
    
    elif value == 61:
        r = ap.Aim_SetToolInfoFilePath(aimHandle,toolPath,True)
        print("Tool Path:",ap.Aim_GetToolInfoFilePath(aimHandle))
        toollist = ap.StringVector(['caliBoard', '18pt', 'cali2','bonePT'])
        while True:
            r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            while r == ap.E_ReturnValue.AIMOOE_NOT_REFLASH:
                time.sleep(0.01)
                r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle, interfaceType, markerinfo,hardware)         
                if r != ap.E_ReturnValue.AIMOOE_OK:
                    break
            residualIndex = list(range(markerinfo.MarkerNumber))
            mtoolsrlt = ap.T_AimToolDataResult()
            r=ap.Aim_FindSpecificToolInfo(aimHandle,markerinfo,toollist,mtoolsrlt,3)
            if r == ap.E_ReturnValue.AIMOOE_OK:
                prlt = mtoolsrlt
                while prlt:
                    if prlt.validflag:
                        PI = 3.1415962
                        print(f"Tool found: {prlt.toolname} Mean error {prlt. MeanError} RMS Error {prlt. Rms}")
                        print(f"tool origin: {prlt. OriginCoor[0]}, {prlt. OriginCoor[1]}, {prlt. OriginCoor[2]}")
                        print(f"tool angle: {prlt.rotationvector[0] * 180 / PI}, {prlt.rotationvector[1] * 180 / PI}, {prlt.rotationvector[2] * 180 / PI}")
                        print("Marker Point Coordinates:")
                        for idx in prlt.toolptidx:
                            if idx in residualIndex:
                                residualIndex.remove(idx)
                            if idx < 0:
                                print("0 0 0")
                            else:
                                print(f"{markerinfo.MarkerCoordinate[idx * 3 + 0]} {markerinfo.MarkerCoordinate[idx * 3 + 1]} {markerinfo.MarkerCoordinate[idx * 3 + 2]}")
                        pnext = prlt.next
                        del prlt
                        prlt = pnext
                if len(residualIndex) > 0:
                    print(f"{len(residualIndex)}discrete points:")
                    for i, j in enumerate(residualIndex):
                        print(f"{i}: {markerinfo.MarkerCoordinate[j * 3 + 0]}, {markerinfo.MarkerCoordinate[j * 3 + 1]}, {markerinfo.MarkerCoordinate[j * 3 + 2]}")
                break
            else:
                del prlt
                break
            
        print("End the lookup")  
    
    elif value == 62:
        CTMarkerPoint = np.array([
                                    [-189.789388859475, -83.4998068907247, 2247.92167116227],
                                    [-130.869739724100, -127.612744935898, 2229.51491037209],
                                    [-170.628261385302, -172.885513685218, 2196.26853365091],
                                    [-230.927341230568, -116.157778943286, 2222.15472458089]
                                ], dtype=np.float32)
        CTDstPoint = np.array([-230.927341230568, -116.157778943286, 2222.15472458089], dtype=np.float32)
        
        r=ap.Aim_InitMappingPointSetsForMarkerSpaceReg(aimHandle,CTMarkerPoint,4)
        if r==ap.E_ReturnValue.AIMOOE_OK:
            while True:
                r=ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
                while r == ap.E_ReturnValue.AIMOOE_NOT_REFLASH:
                    time.sleep(0.01)
                    r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle, interfaceType, markerinfo,hardware)      
                    if r != ap.E_ReturnValue.AIMOOE_OK:
                        break
                prlt = ap.T_AimToolDataResult()
                r=ap.Aim_MappingPointSetsForMarkerSpaceReg(aimHandle,markerinfo,prlt,3)
                if r != ap.E_ReturnValue.AIMOOE_OK:
                    print("Registration failed!")
                    continue
                dstPointInOpticalSys = [0.0, 0.0, 0.0]
                if prlt.validflag:
                    PI = 3.1415926
                    print(f"Registration successful!  Average registration error{prlt.MeanError}")
                    print("Coordinates of the marked point in the camera space in the optical positioning system:")
                    for i, idx in enumerate(prlt.toolptidx):
                        if idx < 0:
                            print("0 0 0")
                        else:
                            print(f"{markerinfo.MarkerCoordinate[idx * 3 + 0]}, {markerinfo.MarkerCoordinate[idx * 3 + 1]}, {markerinfo.MarkerCoordinate[idx * 3 + 2]}")
                    
                    RxCTDstPoint = [0.0, 0.0, 0.0]
                    for i in range(3):
                        for j in range(3):
                            RxCTDstPoint[i] += prlt.Rto[i][j] * CTDstPoint[j]
            
                    for i in range(3):
                        dstPointInOpticalSys[i] = RxCTDstPoint[i] + prlt.Tto[i]
            
                    print(f"The coordinates of the target point in the camera space in the optical positioning system:({dstPointInOpticalSys[0]}, {dstPointInOpticalSys[1]}, {dstPointInOpticalSys[2]})")
                    break
                else:
                    print("Registration failed!")
                    
    elif value == 63:
        mToolMadeinfo = ap.t_ToolMadeProInfo()
     #   r = ap.Aim_SetToolInfoFilePath(aimHandle,toolPath,True)
        print("Tool Path",ap.Aim_GetToolInfoFilePath(aimHandle))
        
        r = ap.Aim_InitToolMadeInfo(aimHandle,4,"4pt1219")
        if r!=ap.E_ReturnValue.AIMOOE_OK:
            print("Initialization failed!")
            return
        cntTimes = 0
        while True:
            time.sleep(0.01)
            cntTimes = cntTimes+1
            r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            if r!=ap.E_ReturnValue.AIMOOE_OK:
                continue
            r = ap.Aim_ProceedToolMade(aimHandle,markerinfo,mToolMadeinfo)
            if r!=ap.E_ReturnValue.AIMOOE_OK:
                continue           
            print("Progress",mToolMadeinfo.madeRate * 100)
            
            if mToolMadeinfo.isMadeProFinished == True and cntTimes >= 10:
                break
        if mToolMadeinfo.isMadeProFinished == True:
            ap.Aim_SaveToolMadeRlt(aimHandle,True)
            print("The tool file was successfully saved!")
        else:
            ap.Aim_SaveToolMadeRlt(aimHandle,False)
            print("Failed to save the tool file!")
    
    elif value == 64:
        mToolFixinfo = ap.t_ToolFixProInfo()
        r = ap.Aim_SetToolInfoFilePath(aimHandle,toolPath,True)
        print("Tool Path:",ap.Aim_GetToolInfoFilePath(aimHandle))
        mToolFixinfo.totalmarkcnt = ap.Aim_InitToolSelfCalibrationWithToolId(aimHandle,"tip2")
        if mToolFixinfo.totalmarkcnt == -1:
            return
        cntTimes = 0
        while True:
            time.sleep(0.01)
            cntTimes = cntTimes + 1
            r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            if r!=ap.E_ReturnValue.AIMOOE_OK:
                continue
            r = ap.Aim_ProceedToolSelfCalibration(aimHandle,markerinfo,mToolFixinfo)
            print("Number of valid calibrations:",mToolFixinfo.isValidFixCnt)
            
            if mToolFixinfo.isCalibrateFinished == True and cntTimes >= 10:
                break
        if mToolFixinfo.isCalibrateFinished and mToolFixinfo.MatchError<0.5:
            ap.Aim_SaveToolSelfCalibration(aimHandle,ap.E_ToolFixRlt.eToolFixSave)
            print("Tool calibration completed, accuracy (mm):",mToolFixinfo.MatchError)
        else:
            ap.Aim_SaveToolSelfCalibration(aimHandle,ap.E_ToolFixRlt.eToolFixCancle)
            print("The tool calibration was not successful")
            
    elif value == 65:
        toolTipInfo = ap.t_ToolTipCalProInfo()
        toolTipInfo.isCalibrateFinished = False
        mToolFixinfo = ap.t_ToolFixProInfo()
        r = ap.Aim_SetToolInfoFilePath(aimHandle,toolPath,True)
        print("Tool Path:",ap.Aim_GetToolInfoFilePath(aimHandle))
        
        r = ap.Aim_InitToolTipCalibrationWithToolId(aimHandle,"CTS-B4B0-006-1","tip2")
        
        if r != ap.E_ReturnValue.AIMOOE_OK:
            return
        cntTimes = 0
        while True:
            time.sleep(0.01)
            cntTimes = cntTimes + 1
            r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            if r!=ap.E_ReturnValue.AIMOOE_OK:
                continue
            r = ap.Aim_ProceedToolTipCalibration(aimHandle,markerinfo,toolTipInfo)
            print("Progress:",int(toolTipInfo.CalibrateRate*100))
            
            if toolTipInfo.isCalibrateFinished == True and cntTimes >= 10:
                break
        if toolTipInfo.isCalibrateFinished and toolTipInfo.CalRMSError<0.5:
            ap.Aim_SaveToolTipCalibration(aimHandle)
            print("Tool calibration completed, accuracy (mm):",toolTipInfo.CalRMSError)
        else:
            print("Tool tip registration was unsuccessful")
            
    elif value == 66:
        accToolRlt = ap.T_AccuracyToolResult()
        r = ap.Aim_SetToolInfoFilePath(aimHandle,toolPath,True)
        print("Tool Path:",ap.Aim_GetToolInfoFilePath(aimHandle))
        
        r = ap.Aim_InitAccuracyCheckTool(aimHandle,"AAK-whole","AAK-left","AAK-right")#"AAS-B8CD1","AAS-B4C1","AAS-B4D1")
        if r != ap.E_ReturnValue.AIMOOE_OK:
            return
        
        for i in range(20):
            time.sleep(0.1)
            r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            if r!=ap.E_ReturnValue.AIMOOE_OK:
                continue
            markerArr = []
            for j in range(markerinfo.MarkerNumber):
                x = markerinfo.MarkerCoordinate[j*3+0]
                y = markerinfo.MarkerCoordinate[j*3+1]
                z = markerinfo.MarkerCoordinate[j*3+2]
                markerArr.append([x,y,z])
            markerArr_np = np.array(markerArr,dtype = np.float64)
            
            r = ap.Aim_AccuracyCheckTool(aimHandle,markerArr_np,markerinfo.MarkerNumber,accToolRlt)
            if accToolRlt.validflag == True:
                print(f"{accToolRlt.Angle[0]} {accToolRlt.Angle[1]} {accToolRlt.Angle[2]} {accToolRlt.Dis}")

        accResult = ap.Aim_AccuracyCheckToolCalculateError(aimHandle)
        print(f"Mean of center distance error: {accResult[0]}  Center distance error discreteness{accResult[1]} Mean Angular Deviation:{accResult[2][0],accResult[2][1],accResult[2][2]}")
    
    elif value == 67:
        data = ap.T_ToolFileData()
        r = ap.Aim_CheckToolFile(aimHandle,toolPath+"tip2.aimtool",data)
        print("Tool name",data.toolname)
        print("Tool Type",data.tooType)
        print("TThe number of amrker in the tool",data.markerNumbers)
        
        num = data.markerNumbers
        if num > 16:
            num = 16
        
        for i in range(num):
            print(f"{i}: {data.MarkerCoordinate[i * 3 + 0]}, {data.MarkerCoordinate[i * 3 + 1]}, {data.MarkerCoordinate[i * 3 + 2]}")
        
        print("tooltip:",data.tipHeadCoordinate[0],data.tipHeadCoordinate[0],data.tipHeadCoordinate[0])
        print("toolmid:",data.tipBodyCoordinate[1],data.tipBodyCoordinate[1],data.tipBodyCoordinate[1])
        
        if r == ap.E_ReturnValue.AIMOOE_OK:
            print("Check complete")
        else:
            print("The check failed")
            
    elif value == 75:
        r = ap.Aim_SetToolInfoFilePath(aimHandle,toolPath,True)
        print("Tool Path:",ap.Aim_GetToolInfoFilePath(aimHandle))
        toolTipInfo = ap.T_ToolTipPivotInfo()
        toolTipInfo.isPivotFinished = False
        
        r = ap.Aim_InitToolTipPivotWithToolId(aimHandle,"tip2",True)
        if r != ap.E_ReturnValue.AIMOOE_OK:
            return
        cntTimes = 0
        time.sleep(4)
        while True:
            time.sleep(0.05)
            cntTimes = cntTimes+1
            r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            if r!=ap.E_ReturnValue.AIMOOE_OK:
                continue
            r = ap.Aim_ProceedToolTipPivot(aimHandle,markerinfo,toolTipInfo)
            print("Progress:",int(toolTipInfo.pivotRate*100))
            
            if toolTipInfo.isPivotFinished == True and cntTimes >= 10:
                break
        if toolTipInfo.isPivotFinished and toolTipInfo.pivotMeanError<1:
            ap.Aim_SaveToolTipCalibration(aimHandle)
            print("Tool calibration completed, accuracy (mm):",toolTipInfo.pivotMeanError)
            
        else:
            print("The tool tip registration is unsuccessful, and the error is greater than 1mm")
    
    elif value == 76:
        toolTipInfo = ap.t_ToolTipCalProInfo()
        toolTipInfo.isCalibrateFinished = False
        r = ap.Aim_SetToolInfoFilePath(aimHandle,toolPath,True)
        print("Tool Path：",ap.Aim_GetToolInfoFilePath(aimHandle))
        
        r = ap.Aim_InitToolCoordinateRenewWithToolId(aimHandle,"EDGE-CALIB","PT4M-EDGE")
        if r != ap.E_ReturnValue.AIMOOE_OK:
            return
        cntTimes = 0
        while True:
            time.sleep(0.01)
            cntTimes = cntTimes+1
            r = ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            if r!=ap.E_ReturnValue.AIMOOE_OK:
                continue
            r = ap.Aim_ProceedToolCoordinateRenew(aimHandle,markerinfo,toolTipInfo)
            print("Progress:",int(toolTipInfo.CalibrateRate))
            
            if toolTipInfo.isCalibrateFinished == True and cntTimes >= 1000:
                break
        if toolTipInfo.isCalibrateFinished and toolTipInfo.CalRMSError<0.5:
            ap.Aim_SaveToolCoordinateRenew(aimHandle)
            print("registration completed, accuracy (mm):",toolTipInfo.CalRMSError)
            
        else:
            print("tool registration was unsuccessful")
        
                
        
if __name__ == "__main__":

    aimHandle = None
    aimHandle = ap.Aim_API_Initial()
    from pathlib import Path
    currentDir = Path(__file__).resolve().parent    
    toolPath = str(currentDir / 'Aimtools')
    #The connection is successful
    if aimHandle is not None:
        # The current Aimpositon connection mode is: USB
        interfaceType = ap.E_Interface.I_ETHERNET
        pospara = ap.T_AIMPOS_DATAPARA()
        result = ap.Aim_ConnectDevice(aimHandle, interfaceType, pospara)
 
        if result == ap.E_ReturnValue.AIMOOE_OK:
            #The connection is successful, continue with other operations
            markerinfo = ap.T_MarkerInfo()
            hardware = ap.T_AimPosStatusInfo()
            resDataSingle = ap.T_AimToolDataResultSingle()
            manufactureInfo = ap.T_ManufactureInfo()
            mtool = ap.T_AimToolDataResult()
            success = False
            ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_NONE)
            ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            ap.Aim_SetToolInfoFilePath(aimHandle,toolPath,True)
            # toollist = ap.StringVector(['caliBoard.aimtool', 'smallone', 'cali2'])
            # ap.Aim_FindSpecificToolInfo(aimHandle,markerinfo,toollist,mtool,3)
            while success != True:
                caseTitle()
                userCase = input("The AimPosition is successfully connected to the AimPosition by USB,please output the case to be executed:")
                whichcase(int(userCase))
            
            # ap.Aim_SetAcquireData(aimHandle,interfaceType,ap.E_DataType.DT_NONE)

            # ap.Aim_GetMarkerAndStatusFromHardware(aimHandle,interfaceType,markerinfo,hardware)
            # ap.Aim_SetToolInfoFilePath(aimHandle,'D:/AimPosAppSolutionAPI_V234-hwz/AimToolBox/Config/AimTools/')

            # toollist = ap.StringVector(['caliBoard', 'smallone', 'value3'])
            # ap.Aim_FindSingleToolInfo(aimHandle, markerinfo, toollist[0], resDataSingle,3)
            # imageC = ap.Aim_GetColorImageFromHardware(aimHandle,interfaceType,pospara)
        else:
            #连接失败
            print("The connection failed")
    else:
        # 初始化失败
        print("If the initialization fails, restart the AimPosition")


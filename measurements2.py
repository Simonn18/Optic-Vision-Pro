# Python script allowing automatic measurement of retinal vessels in fundus images

#     Copyright (C) 2025 DULAU Idris

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.

#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import cv2
import sys
import csv
import tqdm
import numpy
import scipy
import skimage

COLORZONEOD = 50
COLORZONEA = 100
COLORZONEB = 150
COLORZONEC = 200

def exportToCSV(measuresDict, writeFile):
    csvFilePath = writeFile
    with open(csvFilePath, mode='w', newline='') as file:
        fieldnames = list(measuresDict.values())[0].keys() if measuresDict else []
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        for imageName, measures in measuresDict.items():
            writer.writerow({
                fieldname: measures[fieldname] for fieldname in fieldnames
            })
    print("Written to CSV file.")

def getCircleFromOD(od,mode="max"):
    contours, _ = cv2.findContours(od, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        raise "no contour found"
    elif len(contours) > 1:
        raise "more than one CC found"

    x, y, w, h = cv2.boundingRect(contours[0])
    if mode == "min":
        radius = min(w, h) // 2 # Half the minimum side of the bounding box
    else:
        radius = max(w, h) // 2 # Half the maximum side of the bounding box
    centerX = x + w // 2
    centerY = y + h // 2

    mask = numpy.zeros_like(od) 
    mask = cv2.circle(mask, (centerX, centerY), radius, 255, -1)
    return mask

def getZone(image, od, zone):
    contours, _ = cv2.findContours(od, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    x, y, w, h = cv2.boundingRect(contours[0])
    radiusOD = max(w, h) // 2
    centerX = x + w // 2
    centerY = y + h // 2
    odCenter = (centerX,centerY)

    radiusZoneA = radiusOD*2
    radiusZoneB = radiusOD*3
    radiusZoneC = radiusOD*5

    mask = numpy.zeros_like(image, numpy.uint8)
    cv2.circle(mask, odCenter, radiusZoneC, COLORZONEC, -1) #Zone C-B
    cv2.circle(mask, odCenter, radiusZoneB, COLORZONEB, -1) #Zone B
    cv2.circle(mask, odCenter, radiusZoneA, COLORZONEA, -1) #Zone A
    cv2.circle(mask, odCenter, radiusOD, COLORZONEOD, -1)   #OD
    
    maskFull = numpy.copy(mask)

    areaOD = numpy.pi * (radiusOD)**2
    areaZoneA = numpy.pi * (radiusZoneA)**2 - areaOD 
    areaZoneB = numpy.pi * (radiusZoneB)**2 - areaZoneA - areaOD
    areaZoneC = numpy.pi * (radiusZoneC)**2 - areaZoneA - areaOD
    
    visibleAreaOD = numpy.count_nonzero(mask == COLORZONEOD)
    visibleAreaZoneA = numpy.count_nonzero(mask == COLORZONEA)
    visibleAreaZoneB = numpy.count_nonzero(mask == COLORZONEB)
    visibleAreaZoneC = numpy.count_nonzero(mask == COLORZONEC) + visibleAreaZoneB
    visibleAreaZoneOut = numpy.prod(image.shape)-visibleAreaZoneC-visibleAreaZoneA-visibleAreaOD
    visibleAreaZoneAll = numpy.prod(image.shape)-visibleAreaOD    
    
    def getRatesOfWhitePixels(zoneImg, zoneMask, area, visibleArea, colorZone):
        wprT = round(numpy.count_nonzero(zoneImg == 255)/visibleArea*100)
        vzrT = min(100,round(visibleArea/area*100))

        contours, _ = cv2.findContours(zoneMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        x, y, w, h = cv2.boundingRect(contours[0])

        zoneMaskN = numpy.zeros_like(zoneMask)
        cv2.drawContours(zoneMaskN, [numpy.array([(x,y),(x+w,y),odCenter])], 0, 255, -1) #N
        zoneMaskN = zoneMaskN & zoneMask
        zoneImgN = numpy.copy(zoneImg)
        zoneImgN[zoneMaskN == 0] = 0
        wprN = round(numpy.count_nonzero(zoneImgN == 255)/visibleArea*400)
        visibleAreaSubZone = numpy.count_nonzero(zoneMaskN == colorZone)
        vzrN = min(100,round(visibleAreaSubZone/area*400))

        zoneMaskE = numpy.zeros_like(zoneMask)
        cv2.drawContours(zoneMaskE, [numpy.array([(x+w,y),(x+w,y+h),odCenter])], 0, 255, -1) #E*
        zoneMaskE = zoneMaskE & zoneMask
        zoneImgE = numpy.copy(zoneImg)
        zoneImgE[zoneMaskE == 0] = 0
        wprE = round(numpy.count_nonzero(zoneImgE == 255)/visibleArea*400)
        visibleAreaSubZone = numpy.count_nonzero(zoneMaskE == colorZone)
        vzrE = min(100,round(visibleAreaSubZone/area*400))

        zoneMaskS = numpy.zeros_like(zoneMask)
        cv2.drawContours(zoneMaskS, [numpy.array([(x,y+h),(x+w,y+h),odCenter])], 0, 255, -1) #S
        zoneMaskS = zoneMaskS & zoneMask
        zoneImgS = numpy.copy(zoneImg)
        zoneImgS[zoneMaskS == 0] = 0
        wprS = round(numpy.count_nonzero(zoneImgS == 255)/visibleArea*400)
        visibleAreaSubZone = numpy.count_nonzero(zoneMaskS == colorZone)
        vzrS = min(100,round(visibleAreaSubZone/area*400))

        zoneMaskW = numpy.zeros_like(zoneMask)
        cv2.drawContours(zoneMaskW, [numpy.array([(x,y),(x,y+h),odCenter])], 0, 255, -1) #W
        zoneMaskW = zoneMaskW & zoneMask
        zoneImgW = numpy.copy(zoneImg)
        zoneImgW[zoneMaskW == 0] = 0        
        wprW = round(numpy.count_nonzero(zoneImgW == 255)/visibleArea*400)
        visibleAreaSubZone = numpy.count_nonzero(zoneMaskW == colorZone)
        vzrW = min(100,round(visibleAreaSubZone/area*400))

        return wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW

    #subImage, visibleAreaOfTheZone, totalWhitePixelsRate
    if zone == "All":
        zoneImgAll = numpy.copy(image)
        zoneImgAll[mask == COLORZONEOD] = 0
        zoneMaskAll = numpy.ones_like(mask)*255
        zoneMaskAll[mask == COLORZONEOD] = 0
        wprT = round(numpy.count_nonzero(zoneImgAll == 255)/visibleAreaZoneAll*100)
        return maskFull, zoneImgAll, zoneMaskAll, wprT, 100, wprT, 100, wprT, 100, wprT, 100, wprT, 100
    
    elif zone == "A":
        zoneImgA = numpy.copy(image)
        zoneImgA[mask != COLORZONEA] = 0
        zoneMaskA = numpy.copy(mask)
        zoneMaskA[mask != COLORZONEA] = 0
        wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getRatesOfWhitePixels(zoneImgA, zoneMaskA, areaZoneA, visibleAreaZoneA, COLORZONEA)
        return maskFull, zoneImgA, zoneMaskA, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW
    
    elif zone == "B":
        zoneImgB = numpy.copy(image)
        zoneImgB[mask != COLORZONEB] = 0
        zoneMaskB = numpy.copy(mask)
        zoneMaskB[mask != COLORZONEB] = 0
        wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getRatesOfWhitePixels(zoneImgB, zoneMaskB, areaZoneB, visibleAreaZoneB, COLORZONEB)
        return maskFull, zoneImgB, zoneMaskB, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW
    
    elif zone == "C":
        zoneImgC = numpy.copy(image)
        zoneImgC[(mask != COLORZONEC) & (mask != COLORZONEB)] = 0
        zoneMaskC = numpy.copy(mask)
        zoneMaskC[(mask != COLORZONEC) & (mask != COLORZONEB)] = 0
        wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getRatesOfWhitePixels(zoneImgC, zoneMaskC, areaZoneC, visibleAreaZoneC, COLORZONEC)
        return maskFull, zoneImgC, zoneMaskC, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW
       
    elif zone == "Out":
        zoneImgOut = numpy.copy(image)
        zoneImgOut[(mask == COLORZONEC) | (mask == COLORZONEB) | (mask == COLORZONEA) | (mask == COLORZONEOD)] = 0
        zoneMaskOut = numpy.ones_like(mask)*255
        zoneMaskOut[(mask == COLORZONEC) | (mask == COLORZONEB) | (mask == COLORZONEA) | (mask == COLORZONEOD)] = 0
        wprT = round(numpy.count_nonzero(zoneImgOut == 255)/visibleAreaZoneOut*100)
        return maskFull, zoneImgOut, zoneMaskOut, wprT, 100, wprT, 100, wprT, 100, wprT, 100, wprT, 100
      
    else:
        return

def getLonguestCC(image, threshold):
    arr = numpy.copy(image)
    numLabels, labels, stats, centroids = cv2.connectedComponentsWithStats(arr.astype(numpy.uint8), connectivity=8)
    
    labelOfLonguest = -1 
    farthestDist = -1
    for label in range(1, numLabels):
        labelsList = numpy.argwhere(labels == label)
        assert(len(labelsList)>0)
        if len(labelsList) == 1:
            currentFarthest = 1
        else:
            distMatrix = scipy.spatial.distance.pdist(labelsList, metric='euclidean')
            currentFarthest = numpy.max(distMatrix)

        if currentFarthest > farthestDist:
            labelOfLonguest = label
            farthestDist = currentFarthest

    arr[labels != labelOfLonguest] = 0
    return arr

def getEndCrossPointsList(skeleton):
    kernel = numpy.array([[1, 1, 1], [1, 10, 1], [1, 1, 1]])
    neighboursCount = scipy.signal.convolve2d(skeleton, kernel, mode="same")

    endPointsList = numpy.argwhere(neighboursCount==11)
    endPointsListSingle = numpy.argwhere(neighboursCount==10)
    endPointsList = numpy.concatenate((endPointsList, endPointsListSingle))

    crossPointsList = numpy.argwhere(neighboursCount>=13)
    return endPointsList, crossPointsList

def getBorderMask(maskFull, zoneName):
    if zoneName == "A":
        borderMask = numpy.zeros_like(maskFull)
        borderMask[maskFull == COLORZONEOD] = 1
    elif zoneName == "B" or zoneName == "C":
        borderMask = numpy.zeros_like(maskFull)
        borderMask[(maskFull == COLORZONEA) | (maskFull == COLORZONEOD)] = 1
    elif zoneName == "Out":
        borderMask = numpy.zeros_like(maskFull)
        borderMask[(maskFull == COLORZONEC) | (maskFull == COLORZONEB) | (maskFull == COLORZONEA) | (maskFull == COLORZONEOD)] = 1
    elif zoneName == "All":
        borderMask = numpy.zeros_like(maskFull)
        borderMask[maskFull == COLORZONEOD] = 1
    return borderMask

def getCalibersListFirstCross(image, skeleton, borderMask):
    borderMaskDilated = cv2.dilate(numpy.copy(borderMask), numpy.ones((3,3)))
    borderMaskZone = borderMaskDilated & numpy.where(borderMask==1,0,1)

    inPointsList = numpy.argwhere(borderMaskZone)     
    endPointsList, crossPointsList = getEndCrossPointsList(skeleton)
    endPointsListODNeighbors = [e for e in endPointsList if any(numpy.array_equal(e, p) for p in inPointsList)]

    cutSK = numpy.copy(skeleton)
    for x,y in crossPointsList:
        cutSK[x,y] = 0

    numLabelsSK, labelsSK, statsSK, _ = cv2.connectedComponentsWithStats(cutSK.astype(numpy.uint8), connectivity=8)

    newSK = numpy.zeros_like(skeleton)
    for x,y in endPointsListODNeighbors:
        newSK[labelsSK == labelsSK[x,y]] = 1
    contours, hierarchy = cv2.findContours(newSK.astype(numpy.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    imgCopy = numpy.copy(image)
    newImg = numpy.zeros_like(skeleton).astype(numpy.uint8)
    for cc in contours:
        x, y, w, h = cv2.boundingRect(cc)
        croppedImg = getLonguestCC(imgCopy[y:y+h,x:x+w], 1)
        newImg[y:y+h,x:x+w] = newImg[y:y+h,x:x+w] | croppedImg

    # cv2.imshow("newImg",newImg)
    # cv2.imshow("newSK",newSK.astype(numpy.uint8)*255)
    # cv2.waitKey(0)

    return getCalibersList(newImg, newSK)

def getCalibersList(image, skeleton): 
    _, _, statsSK, _ = cv2.connectedComponentsWithStats(skeleton.astype(numpy.uint8), connectivity=8)
    lengthsList = list(statsSK[1:, cv2.CC_STAT_AREA])
    
    _, _, statsIMG, _ = cv2.connectedComponentsWithStats(image.astype(numpy.uint8), connectivity=8)
    areasList = list(statsIMG[1:, cv2.CC_STAT_AREA])
  
    if len(areasList) != len(lengthsList):
        skeleton = skimage.morphology.skeletonize(image) 
        _, _, statsSK, _ = cv2.connectedComponentsWithStats(skeleton.astype(numpy.uint8), connectivity=8)
        lengthsList = list(statsSK[1:, cv2.CC_STAT_AREA])

    calibersList = [a / b for a,b in zip(areasList, lengthsList)]

    return calibersList

def getMeanCaliber(calibersList):
    return numpy.mean(calibersList)

def getStandardDeviation(calibersList):
    return numpy.std(calibersList)

def getMeanBigXCaliber(calibersList):
    X = min(6,len(calibersList))
    subBigXCalibersList = sorted(calibersList, reverse=True)[:X]
    return getMeanCaliber(subBigXCalibersList), X

def getStandardDeviationBigXCaliber(calibersList):
    X = min(6,len(calibersList))
    subBigXCalibersList = sorted(calibersList, reverse=True)[:X]
    return getStandardDeviation(subBigXCalibersList), X

def getMeanBigXCaliberAVRatio(meanBigXCaliberArteries, meanBigXCaliberVeins):
    return meanBigXCaliberArteries/meanBigXCaliberVeins

def boxcount(im, bins=10):
    r"""
    Calculates fractal dimension of an image using the tiled box counting
    method [1]_

    Parameters
    ----------
    im : ndarray
        The image of the porous material.
    bins : int or array_like, optional
        The number of box sizes to use. The default is 10 sizes
        logarithmically spaced between 1 and ``min(im.shape)``.
        If an array is provided, this is used directly.

    Returns
    -------
    results
        An object possessing the following attributes:

        size : ndarray
            The box sizes used
        count : ndarray
            The number of boxes of each size that contain both solid and void
        slope : ndarray
            The gradient of ``count``. This has the same number of elements as
            ``count`` and

    References
    ----------
    .. [1] See Boxcounting on `Wikipedia <https://en.wikipedia.org/wiki/Box_counting>`_

    Examples
    --------
    `Click here
    <https://porespy.org/examples/metrics/reference/box_counting.html>`_
    to view online example.

    """
    im = numpy.array(im, dtype=bool)

    if (len(im.shape) != 2 and len(im.shape) != 3):
        raise Exception('Image must be 2-dimensional or 3-dimensional')

    if isinstance(bins, int):
        Ds = numpy.unique(numpy.logspace(1, numpy.log10(min(im.shape)), bins).astype(int))
    else:
        Ds = numpy.array(bins).astype(int)

    N = []
    for d in Ds:
        result = 0
        for i in range(0, im.shape[0], d):
            for j in range(0, im.shape[1], d):
                if len(im.shape) == 2:
                    temp = im[i:i+d, j:j+d]
                    result += numpy.any(temp)
                    result -= numpy.all(temp)
                else:
                    for k in range(0, im.shape[2], d):
                        temp = im[i:i+d, j:j+d, k:k+d]
                        result += numpy.any(temp)
                        result -= numpy.all(temp)
        N.append(result)
    slope = -1*numpy.gradient(numpy.log(numpy.array(N)), numpy.log(Ds))
    return slope

def getFractalDimension(skeleton):
    slope = boxcount(skeleton, 10)
    return numpy.mean(slope)
    
def getDistance(p1, p2, mode):
    if mode == "euclidean":
        return scipy.spatial.distance.euclidean(p1,p2)
    elif mode == "cityblock":
        return scipy.spatial.distance.cityblock(p1,p2)
    elif mode == "chebyshev":
        return scipy.spatial.distance.chebyshev(p1,p2)
    else:
        return

def getFiniteDifference(coordinates, idx):
    x,y = coordinates[idx]

    def forwardDifferences(x, y, coordinates):
        nextX, nextY = coordinates[idx + 1]
        dx1, dy1 = nextX - x, nextY - y
        return 2 * (dx1 * dy1) / (numpy.sqrt(dx1**2 + dy1**2)**3)
    
    def centralDifferences(x, y, coordinates):
        prevX, prevY = coordinates[idx - 1]
        nextX, nextY = coordinates[idx + 1]
        dx1, dy1 = x - prevX, y - prevY
        dx2, dy2 = nextX - x, nextY - y
        numerator = dx1 * dy2 - dx2 * dy1
        denominator = (numpy.sqrt(dx1**2 + dy1**2)**3) * (numpy.sqrt(dx2**2 + dy2**2)**3)
        return 2 * numerator / denominator

    def backwardDifferences(x, y, coordinates):
        prevX, prevY = coordinates[idx - 1]
        dx2, dy2 = x - prevX, y - prevY
        return 2 * (dx2 * dy2) / (numpy.sqrt(dx2**2 + dy2**2)**3)

    if idx == 0: 
        return forwardDifferences(x, y, coordinates)
    elif idx == len(coordinates) - 1: 
        return backwardDifferences(x, y, coordinates)
    else: 
        return centralDifferences(x, y, coordinates)

def getFiniteDifferenceList(vesselCoord):
    return [getFiniteDifference(vesselCoord, idx) for idx in range(1,len(vesselCoord))]   

def getTortuosities(skeleton):
    simpleTortuositiesList = []
    curvatureTortuositiesList = []

    #From skeleton extract CC   
    numLabelSK, labelsSK, _, _ = cv2.connectedComponentsWithStats(skeleton.astype(numpy.uint8), connectivity=8)

    #For each CC get crossP ()>=3)
    for label in range(1, numLabelSK):
        subSK = numpy.where(labelsSK == label,1,0)
        endP, crossP = getEndCrossPointsList(subSK)
        
        #Remove crossP
        subSK[crossP] = 0
        
        #extractCC again
        numLabelSubSK, labelsSubSK, _, _ = cv2.connectedComponentsWithStats(subSK.astype(numpy.uint8), connectivity=8)
        for label in range(1, numLabelSubSK):
            subSubSK = numpy.where(labelsSubSK == label,1,0)

            endP, crossP = getEndCrossPointsList(subSubSK)
            if len(endP) < 2:
                simpleTortuosity = 1
                curvatureTortuosity = 0
            else:
                # -------- SIMPLE --------
                pixCount = numpy.sum(subSubSK)   
                chebyshevDist = getDistance(endP[0],endP[-1],"chebyshev")
                simpleTortuosity = (pixCount-1)/chebyshevDist
            
                # -------- CURVATURE -------- 
                vesselCoordinates = numpy.argwhere(labelsSubSK == label)           
                curvaturesList = getFiniteDifferenceList(vesselCoordinates)
                curvatureTortuosity = numpy.mean(numpy.abs(curvaturesList))

            simpleTortuositiesList.append(simpleTortuosity)
            curvatureTortuositiesList.append(curvatureTortuosity)

    sTmean, sTsd, sTmax = numpy.mean(simpleTortuositiesList), numpy.std(simpleTortuositiesList), numpy.max(simpleTortuositiesList)
    cTmean, cTsd, cTmax = numpy.mean(curvatureTortuositiesList), numpy.std(curvatureTortuositiesList), numpy.max(curvatureTortuositiesList)
    return sTmean, sTsd, sTmax, cTmean, cTsd, cTmax

def getStrahlerSkeleton(skeleton, subMask):
    """Two cases where checkSum is not 0:
    1) When all branch pixels are inside the mask zone
    2) When there is a cycle in the graph: Not a tree anymore."""
    currentDepth = 0
    strahlerSK = numpy.zeros_like(skeleton).astype(numpy.uint8)
    outSK = numpy.where((skeleton!=0)&(subMask!=0), 1, 0) #To remove OD zone from skeleton

    borderMask = numpy.where(subMask==0,1,0).astype(numpy.uint8)
    borderMaskDilated = cv2.dilate(numpy.copy(borderMask), numpy.ones((7,7)))
    borderMaskEroded = cv2.erode(numpy.copy(borderMask), numpy.ones((7,7)))
    borderMaskZone = borderMaskDilated & numpy.where(borderMaskEroded==1,0,1)

    inPointsList = numpy.argwhere(borderMaskZone)     
    endPointsList, crossPointsList = getEndCrossPointsList(outSK)
    endPointsFromCCToRemove = [e for e in endPointsList if not any(numpy.array_equal(e, p) for p in inPointsList)]

    while(len(endPointsFromCCToRemove)>0):
        currentDepth += 1
        
        for x,y in crossPointsList:
            outSK[x,y] = 0

        numLabelsSK, labelsSK, statsSK, _ = cv2.connectedComponentsWithStats(outSK.astype(numpy.uint8), connectivity=8)

        for x,y in endPointsFromCCToRemove:
            outSK[labelsSK == labelsSK[x,y]] = 0
            strahlerSK[labelsSK == labelsSK[x,y]] = currentDepth

        outSK = cv2.dilate(outSK.astype(numpy.uint8), numpy.ones((7,7)))
        outSK = skimage.morphology.skeletonize(outSK, method='lee')

        endPointsList, crossPointsList = getEndCrossPointsList(outSK)
        endPointsFromCCToRemove = [e for e in endPointsList if not any(numpy.array_equal(e, p) for p in inPointsList)]

    checkSum = numpy.sum(outSK) 

    if checkSum>0:
        strahlerSkeletonState = "early stop"
    else:
        strahlerSkeletonState = "completed"
    maxDepth = currentDepth

    return strahlerSK, outSK, maxDepth, strahlerSkeletonState

def getNumberOfCC(ccList):
    return len(ccList)

def getArea(image):
    return numpy.count_nonzero(image)

def getNbEndPoints(skeleton):
    return len(getEndCrossPointsList(skeleton)[0])

def getNbCrossPointsCCs(skeleton):
    _, crossPList = getEndCrossPointsList(skeleton)
    crossPImg = numpy.zeros_like(skeleton).astype(numpy.uint8)
    for x,y in crossPList:
        crossPImg[x,y] = 1
    numLabels, labels, stats, centroids = cv2.connectedComponentsWithStats(crossPImg.astype(numpy.uint8), connectivity=8) 
    return numLabels-1, crossPImg

def getNbOverlapPointsCCs(skeletonAV, crossPImgtA, crossPImgtV):
    _, crossPImgtAV = getNbCrossPointsCCs(skeletonAV)
    overlapImg = numpy.where((crossPImgtAV!=0) & (crossPImgtA==0) & (crossPImgtV==0), 1, 0)
    numLabels, labels, stats, centroids = cv2.connectedComponentsWithStats(overlapImg.astype(numpy.uint8), connectivity=8) 
    return numLabels-1

def main(argv):
    if len(argv) < 5:
        print("Usage: python measurements.py <arteriesPath> <veinsPath> <odPath> <writeFile> [specificImage]")
        return

    arteriesPath = argv[1]
    veinsPath    = argv[2]
    odPath       = argv[3]
    writeFile    = argv[4]
    
    # 2. Gestion du filtre (5ème argument optionnel)
    # Si l'utilisateur donne un nom d'image, on le stocke, sinon c'est None
    target_file = argv[5] if len(argv) > 5 else None

    # 3. Préparation de la liste des fichiers à traiter
    try:
        all_files = sorted(os.listdir(arteriesPath))
    except FileNotFoundError:
        print(f"Erreur : Le dossier {arteriesPath} est introuvable.")
        return

    # Si une image spécifique est demandée, on réduit la liste à ce seul fichier
    if target_file:
        if target_file in all_files:
            file_list = [target_file]
        else:
            print(f"Erreur : Le fichier '{target_file}' n'existe pas dans {arteriesPath}")
            return
    else:
        # Sinon, on traite tout le dossier normalement
        file_list = all_files

    # 4. Boucle de traitement (le reste de ton code original)
    # On utilise maintenant 'file_list' qui contient soit 1 image, soit toutes
    measuresDict = {}

    for imageName in tqdm.tqdm(file_list):
        # Vérification de l'existence dans les autres dossiers (Veines et OD)
        if os.path.exists(os.path.join(veinsPath, imageName)) and \
           os.path.exists(os.path.join(odPath, imageName)):
            arteries = cv2.imread(os.path.join(arteriesPath,imageName), cv2.IMREAD_UNCHANGED)
            veins = cv2.imread(os.path.join(veinsPath,imageName), cv2.IMREAD_UNCHANGED)
            od = cv2.imread(os.path.join(odPath,imageName.split(".")[0]+".png"), cv2.IMREAD_UNCHANGED) #for gt
        
            if numpy.sum(arteries)==0 or numpy.sum(veins)==0 or numpy.sum(od)==0:
                if target_file: return

            od = getCircleFromOD(od, "max")

# measureName_zone_type; zone: [A, B, C, Out, All]; type: [Arteries, Veins, AV]

        #region ============= ZONE A | ARTERIES =============
        zoneName = "A"
        vesselsMode = arteries          

        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_A_Arteries = wprT
        wprN_A_Arteries = wprN
        wprE_A_Arteries = wprE
        wprS_A_Arteries = wprS
        wprW_A_Arteries = wprW

        vzrT_A_Arteries = vzrT
        vzrN_A_Arteries = vzrN
        vzrE_A_Arteries = vzrE
        vzrS_A_Arteries = vzrS
        vzrW_A_Arteries = vzrW       

        # maskZones = numpy.copy(maskFull)
        # skeleton_A_Arteries = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_A_Arteries = meanCaliberFirstCross
        sdCaliberFC_A_Arteries = standardDeviationFirstCross
        meanBigXCaliberFC_A_Arteries = meanBigXCaliberFirstCross
        sdBigXCaliberFC_A_Arteries = standardDeviationBigXCaliberFirstCross
        nbXFC_A_Arteries = XFirstCross

        meanCaliberFull_A_Arteries = meanCaliberFull
        sdCaliberFull_A_Arteries = standardDeviationFull
        meanBigXCaliberFull_A_Arteries = meanBigXCaliberFull
        sdBigXCaliberFull_A_Arteries = standardDeviationBigXCaliberFull
        nbXFull_A_Arteries = XFull
    
        #[FRACTAL]
        fractalDim_A_Arteries = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Arteries = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------
        
        nbCC_A_Arteries = nbCC
        area_A_Arteries = area
        areaSkeleton_A_Arteries = areaSkeleton          
        nbEndP_A_Arteries = nbEndPoints
        nbCrossP_A_Arteries = nbCrossPoints
        #endregion

        #region ============= ZONE A | VEINS  =============
        zoneName = "A"
        vesselsMode = veins            
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_A_Veins = wprT
        wprN_A_Veins = wprN
        wprE_A_Veins = wprE
        wprS_A_Veins = wprS
        wprW_A_Veins = wprW

        vzrT_A_Veins = vzrT
        vzrN_A_Veins = vzrN
        vzrE_A_Veins = vzrE
        vzrS_A_Veins = vzrS
        vzrW_A_Veins = vzrW       

        # skeleton_A_Veins = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_A_Veins = meanCaliberFirstCross
        sdCaliberFC_A_Veins = standardDeviationFirstCross
        meanBigXCaliberFC_A_Veins = meanBigXCaliberFirstCross
        sdBigXCaliberFC_A_Veins = standardDeviationBigXCaliberFirstCross
        nbXFC_A_Veins = XFirstCross

        meanCaliberFull_A_Veins = meanCaliberFull
        sdCaliberFull_A_Veins = standardDeviationFull
        meanBigXCaliberFull_A_Veins = meanBigXCaliberFull
        sdBigXCaliberFull_A_Veins = standardDeviationBigXCaliberFull
        nbXFull_A_Veins = XFull
    
        #[FRACTAL]
        fractalDim_A_Veins = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Veins = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------

        nbCC_A_Veins = nbCC
        area_A_Veins = area
        areaSkeleton_A_Veins = areaSkeleton          
        nbEndP_A_Veins = nbEndPoints
        nbCrossP_A_Veins = nbCrossPoints
        #endregion

        #region ============= ZONE A | COMBINED  =============
        zoneName = "A"
        vesselsMode = arteries | veins         
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------

        #[CALIBERS]
        avrBigXCaliberFC_A_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFC_A_Arteries, meanBigXCaliberFC_A_Veins)
        avrBigXCaliberFull_A_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFull_A_Arteries, meanBigXCaliberFull_A_Veins)

        #[QUANTITY]
        nbOverlapP_A_AV = getNbOverlapPointsCCs(subSkeleton, crossPImg_Arteries, crossPImg_Veins)        
        #endregion

###############################################################

        #region ============= ZONE B | ARTERIES =============
        zoneName = "B"
        vesselsMode = arteries          

        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_B_Arteries = wprT
        wprN_B_Arteries = wprN
        wprE_B_Arteries = wprE
        wprS_B_Arteries = wprS
        wprW_B_Arteries = wprW

        vzrT_B_Arteries = vzrT
        vzrN_B_Arteries = vzrN
        vzrE_B_Arteries = vzrE
        vzrS_B_Arteries = vzrS
        vzrW_B_Arteries = vzrW       

        # skeleton_B_Arteries = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_B_Arteries = meanCaliberFirstCross
        sdCaliberFC_B_Arteries = standardDeviationFirstCross
        meanBigXCaliberFC_B_Arteries = meanBigXCaliberFirstCross
        sdBigXCaliberFC_B_Arteries = standardDeviationBigXCaliberFirstCross
        nbXFC_B_Arteries = XFirstCross

        meanCaliberFull_B_Arteries = meanCaliberFull
        sdCaliberFull_B_Arteries = standardDeviationFull
        meanBigXCaliberFull_B_Arteries = meanBigXCaliberFull
        sdBigXCaliberFull_B_Arteries = standardDeviationBigXCaliberFull
        nbXFull_B_Arteries = XFull
    
        #[FRACTAL]
        fractalDim_B_Arteries = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Arteries = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------
        
        nbCC_B_Arteries = nbCC
        area_B_Arteries = area
        areaSkeleton_B_Arteries = areaSkeleton          
        nbEndP_B_Arteries = nbEndPoints
        nbCrossP_B_Arteries = nbCrossPoints
        #endregion

        #region ============= ZONE B | VEINS  =============
        zoneName = "B"
        vesselsMode = veins            
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_B_Veins = wprT
        wprN_B_Veins = wprN
        wprE_B_Veins = wprE
        wprS_B_Veins = wprS
        wprW_B_Veins = wprW

        vzrT_B_Veins = vzrT
        vzrN_B_Veins = vzrN
        vzrE_B_Veins = vzrE
        vzrS_B_Veins = vzrS
        vzrW_B_Veins = vzrW       

        # skeleton_B_Veins = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_B_Veins = meanCaliberFirstCross
        sdCaliberFC_B_Veins = standardDeviationFirstCross
        meanBigXCaliberFC_B_Veins = meanBigXCaliberFirstCross
        sdBigXCaliberFC_B_Veins = standardDeviationBigXCaliberFirstCross
        nbXFC_B_Veins = XFirstCross

        meanCaliberFull_B_Veins = meanCaliberFull
        sdCaliberFull_B_Veins = standardDeviationFull
        meanBigXCaliberFull_B_Veins = meanBigXCaliberFull
        sdBigXCaliberFull_B_Veins = standardDeviationBigXCaliberFull
        nbXFull_B_Veins = XFull
    
        #[FRACTAL]
        fractalDim_B_Veins = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Veins = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------

        nbCC_B_Veins = nbCC
        area_B_Veins = area
        areaSkeleton_B_Veins = areaSkeleton          
        nbEndP_B_Veins = nbEndPoints
        nbCrossP_B_Veins = nbCrossPoints
        #endregion

        #region ============= ZONE B | COMBINED  =============
        zoneName = "B"
        vesselsMode = arteries | veins         
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------

        #[CALIBERS]
        avrBigXCaliberFC_B_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFC_B_Arteries, meanBigXCaliberFC_B_Veins)
        avrBigXCaliberFull_B_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFull_B_Arteries, meanBigXCaliberFull_B_Veins)

        #[QUANTITY]
        nbOverlapP_B_AV = getNbOverlapPointsCCs(subSkeleton, crossPImg_Arteries, crossPImg_Veins)        
        #endregion

###############################################################

        #region ============= ZONE C | ARTERIES =============
        zoneName = "C"
        vesselsMode = arteries          

        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_C_Arteries = wprT
        wprN_C_Arteries = wprN
        wprE_C_Arteries = wprE
        wprS_C_Arteries = wprS
        wprW_C_Arteries = wprW

        vzrT_C_Arteries = vzrT
        vzrN_C_Arteries = vzrN
        vzrE_C_Arteries = vzrE
        vzrS_C_Arteries = vzrS
        vzrW_C_Arteries = vzrW       

        # skeleton_C_Arteries = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_C_Arteries = meanCaliberFirstCross
        sdCaliberFC_C_Arteries = standardDeviationFirstCross
        meanBigXCaliberFC_C_Arteries = meanBigXCaliberFirstCross
        sdBigXCaliberFC_C_Arteries = standardDeviationBigXCaliberFirstCross
        nbXFC_C_Arteries = XFirstCross

        meanCaliberFull_C_Arteries = meanCaliberFull
        sdCaliberFull_C_Arteries = standardDeviationFull
        meanBigXCaliberFull_C_Arteries = meanBigXCaliberFull
        sdBigXCaliberFull_C_Arteries = standardDeviationBigXCaliberFull
        nbXFull_C_Arteries = XFull
    
        #[FRACTAL]
        fractalDim_C_Arteries = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Arteries = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------
        
        nbCC_C_Arteries = nbCC
        area_C_Arteries = area
        areaSkeleton_C_Arteries = areaSkeleton          
        nbEndP_C_Arteries = nbEndPoints
        nbCrossP_C_Arteries = nbCrossPoints
        #endregion

        #region ============= ZONE C | VEINS  =============
        zoneName = "C"
        vesselsMode = veins            
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_C_Veins = wprT
        wprN_C_Veins = wprN
        wprE_C_Veins = wprE
        wprS_C_Veins = wprS
        wprW_C_Veins = wprW

        vzrT_C_Veins = vzrT
        vzrN_C_Veins = vzrN
        vzrE_C_Veins = vzrE
        vzrS_C_Veins = vzrS
        vzrW_C_Veins = vzrW       

        # skeleton_C_Veins = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_C_Veins = meanCaliberFirstCross
        sdCaliberFC_C_Veins = standardDeviationFirstCross
        meanBigXCaliberFC_C_Veins = meanBigXCaliberFirstCross
        sdBigXCaliberFC_C_Veins = standardDeviationBigXCaliberFirstCross
        nbXFC_C_Veins = XFirstCross

        meanCaliberFull_C_Veins = meanCaliberFull
        sdCaliberFull_C_Veins = standardDeviationFull
        meanBigXCaliberFull_C_Veins = meanBigXCaliberFull
        sdBigXCaliberFull_C_Veins = standardDeviationBigXCaliberFull
        nbXFull_C_Veins = XFull
    
        #[FRACTAL]
        fractalDim_C_Veins = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Veins = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------

        nbCC_C_Veins = nbCC
        area_C_Veins = area
        areaSkeleton_C_Veins = areaSkeleton          
        nbEndP_C_Veins = nbEndPoints
        nbCrossP_C_Veins = nbCrossPoints
        #endregion

        #region ============= ZONE C | COMBINED  =============
        zoneName = "C"
        vesselsMode = arteries | veins         
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------

        #[CALIBERS]
        avrBigXCaliberFC_C_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFC_C_Arteries, meanBigXCaliberFC_C_Veins)
        avrBigXCaliberFull_C_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFull_C_Arteries, meanBigXCaliberFull_C_Veins)

        #[QUANTITY]
        nbOverlapP_C_AV = getNbOverlapPointsCCs(subSkeleton, crossPImg_Arteries, crossPImg_Veins)        
        #endregion

###############################################################

        #region ============= ZONE Out | ARTERIES =============
        zoneName = "Out"
        vesselsMode = arteries          

        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_Out_Arteries = wprT
        wprN_Out_Arteries = wprN
        wprE_Out_Arteries = wprE
        wprS_Out_Arteries = wprS
        wprW_Out_Arteries = wprW

        vzrT_Out_Arteries = vzrT
        vzrN_Out_Arteries = vzrN
        vzrE_Out_Arteries = vzrE
        vzrS_Out_Arteries = vzrS
        vzrW_Out_Arteries = vzrW       

        # skeleton_Out_Arteries = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_Out_Arteries = meanCaliberFirstCross
        sdCaliberFC_Out_Arteries = standardDeviationFirstCross
        meanBigXCaliberFC_Out_Arteries = meanBigXCaliberFirstCross
        sdBigXCaliberFC_Out_Arteries = standardDeviationBigXCaliberFirstCross
        nbXFC_Out_Arteries = XFirstCross

        meanCaliberFull_Out_Arteries = meanCaliberFull
        sdCaliberFull_Out_Arteries = standardDeviationFull
        meanBigXCaliberFull_Out_Arteries = meanBigXCaliberFull
        sdBigXCaliberFull_Out_Arteries = standardDeviationBigXCaliberFull
        nbXFull_Out_Arteries = XFull
    
        #[FRACTAL]
        fractalDim_Out_Arteries = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Arteries = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------
        
        nbCC_Out_Arteries = nbCC
        area_Out_Arteries = area
        areaSkeleton_Out_Arteries = areaSkeleton          
        nbEndP_Out_Arteries = nbEndPoints
        nbCrossP_Out_Arteries = nbCrossPoints
        #endregion

        #region ============= ZONE C | VEINS  =============
        zoneName = "Out"
        vesselsMode = veins            
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_Out_Veins = wprT
        wprN_Out_Veins = wprN
        wprE_Out_Veins = wprE
        wprS_Out_Veins = wprS
        wprW_Out_Veins = wprW

        vzrT_Out_Veins = vzrT
        vzrN_Out_Veins = vzrN
        vzrE_Out_Veins = vzrE
        vzrS_Out_Veins = vzrS
        vzrW_Out_Veins = vzrW       

        # skeleton_Out_Veins = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_Out_Veins = meanCaliberFirstCross
        sdCaliberFC_Out_Veins = standardDeviationFirstCross
        meanBigXCaliberFC_Out_Veins = meanBigXCaliberFirstCross
        sdBigXCaliberFC_Out_Veins = standardDeviationBigXCaliberFirstCross
        nbXFC_Out_Veins = XFirstCross

        meanCaliberFull_Out_Veins = meanCaliberFull
        sdCaliberFull_Out_Veins = standardDeviationFull
        meanBigXCaliberFull_Out_Veins = meanBigXCaliberFull
        sdBigXCaliberFull_Out_Veins = standardDeviationBigXCaliberFull
        nbXFull_Out_Veins = XFull
    
        #[FRACTAL]
        fractalDim_Out_Veins = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Veins = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------

        nbCC_Out_Veins = nbCC
        area_Out_Veins = area
        areaSkeleton_Out_Veins = areaSkeleton          
        nbEndP_Out_Veins = nbEndPoints
        nbCrossP_Out_Veins = nbCrossPoints
        #endregion

        #region ============= ZONE C | COMBINED  =============
        zoneName = "Out"
        vesselsMode = arteries | veins         
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------

        #[CALIBERS]
        avrBigXCaliberFC_Out_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFC_Out_Arteries, meanBigXCaliberFC_Out_Veins)
        avrBigXCaliberFull_Out_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFull_Out_Arteries, meanBigXCaliberFull_Out_Veins)

        #[QUANTITY]
        nbOverlapP_Out_AV = getNbOverlapPointsCCs(subSkeleton, crossPImg_Arteries, crossPImg_Veins)        
        #endregion

###############################################################


        #region ============= ZONE All | ARTERIES =============
        zoneName = "All"
        vesselsMode = arteries          

        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_All_Arteries = wprT
        wprN_All_Arteries = wprN
        wprE_All_Arteries = wprE
        wprS_All_Arteries = wprS
        wprW_All_Arteries = wprW

        vzrT_All_Arteries = vzrT
        vzrN_All_Arteries = vzrN
        vzrE_All_Arteries = vzrE
        vzrS_All_Arteries = vzrS
        vzrW_All_Arteries = vzrW       

        # skeleton_All_Arteries = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_All_Arteries = meanCaliberFirstCross
        sdCaliberFC_All_Arteries = standardDeviationFirstCross
        meanBigXCaliberFC_All_Arteries = meanBigXCaliberFirstCross
        sdBigXCaliberFC_All_Arteries = standardDeviationBigXCaliberFirstCross
        nbXFC_All_Arteries = XFirstCross

        meanCaliberFull_All_Arteries = meanCaliberFull
        sdCaliberFull_All_Arteries = standardDeviationFull
        meanBigXCaliberFull_All_Arteries = meanBigXCaliberFull
        sdBigXCaliberFull_All_Arteries = standardDeviationBigXCaliberFull
        nbXFull_All_Arteries = XFull
    
        #[FRACTAL]
        fractalDim_All_Arteries = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Arteries = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------
        
        nbCC_All_Arteries = nbCC
        area_All_Arteries = area
        areaSkeleton_All_Arteries = areaSkeleton          
        nbEndP_All_Arteries = nbEndPoints
        nbCrossP_All_Arteries = nbCrossPoints

        #[TORTUOSITY]
        sTmean, sTsd, sTmax, cTmean, cTsd, cTmax = getTortuosities(subSkeleton)
        # ----------------------------------------------------------------------
        meanSiTort_All_Arteries = sTmean
        sdSiTort_All_Arteries = sTsd
        maxSiTort_All_Arteries = sTmax

        meanCuTort_All_Arteries = cTmean
        sdCuTort_All_Arteries = cTsd
        maxCuTort_All_Arteries = cTmax

        #[DEPTH]
        strahlerSK, outSK, maxDepth, checkSum = getStrahlerSkeleton(skeletonFull, subMask)
        # ----------------------------------------------------------------------
        # strahlerSkeleton_All_Arteries = strahlerSK
        # residualStrahlerSkeleton_All_Arteries = outSK

        maxDepth_All_Arteries = maxDepth
        residualState_All_Arteries = checkSum
        #endregion

        #region ============= ZONE C | VEINS  =============
        zoneName = "All"
        vesselsMode = veins            
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------
        
        #[ZONES]
        wprT_All_Veins = wprT
        wprN_All_Veins = wprN
        wprE_All_Veins = wprE
        wprS_All_Veins = wprS
        wprW_All_Veins = wprW

        vzrT_All_Veins = vzrT
        vzrN_All_Veins = vzrN
        vzrE_All_Veins = vzrE
        vzrS_All_Veins = vzrS
        vzrW_All_Veins = vzrW       

        skeleton_All_Veins = numpy.copy(subSkeleton)

        #[CALIBERS]
        calibersListFirstCross = getCalibersListFirstCross(subImage, subSkeleton, getBorderMask(maskFull, zoneName))
        meanCaliberFirstCross = getMeanCaliber(calibersListFirstCross)
        standardDeviationFirstCross = getStandardDeviation(calibersListFirstCross)
        meanBigXCaliberFirstCross, XFirstCross = getMeanBigXCaliber(calibersListFirstCross)
        standardDeviationBigXCaliberFirstCross, _ = getStandardDeviationBigXCaliber(calibersListFirstCross)

        calibersListFull = getCalibersList(subImage, subSkeleton)
        meanCaliberFull = getMeanCaliber(calibersListFull)
        standardDeviationFull = getStandardDeviation(calibersListFull)
        meanBigXCaliberFull, XFull = getMeanBigXCaliber(calibersListFull)
        standardDeviationBigXCaliberFull, _ = getStandardDeviationBigXCaliber(calibersListFull)
        # ----------------------------------------------------------------------

        meanCaliberFC_All_Veins = meanCaliberFirstCross
        sdCaliberFC_All_Veins = standardDeviationFirstCross
        meanBigXCaliberFC_All_Veins = meanBigXCaliberFirstCross
        sdBigXCaliberFC_All_Veins = standardDeviationBigXCaliberFirstCross
        nbXFC_All_Veins = XFirstCross

        meanCaliberFull_All_Veins = meanCaliberFull
        sdCaliberFull_All_Veins = standardDeviationFull
        meanBigXCaliberFull_All_Veins = meanBigXCaliberFull
        sdBigXCaliberFull_All_Veins = standardDeviationBigXCaliberFull
        nbXFull_All_Veins = XFull
    
        #[FRACTAL]
        fractalDim_All_Veins = getFractalDimension(subSkeleton)

        #[QUANTITY]
        nbCC = getNumberOfCC(calibersListFull)
        area = getArea(subImage)
        areaSkeleton = getArea(subSkeleton)          
        nbEndPoints = getNbEndPoints(subSkeleton)
        nbCrossPoints,crossPImg_Veins = getNbCrossPointsCCs(subSkeleton) #crossPImg_A used for combined
        # ----------------------------------------------------------------------

        nbCC_All_Veins = nbCC
        area_All_Veins = area
        areaSkeleton_All_Veins = areaSkeleton          
        nbEndP_All_Veins = nbEndPoints
        nbCrossP_All_Veins = nbCrossPoints
        
        #[TORTUOSITY]
        sTmean, sTsd, sTmax, cTmean, cTsd, cTmax = getTortuosities(subSkeleton)
        # ----------------------------------------------------------------------
        meanSiTort_All_Veins = sTmean
        sdSiTort_All_Veins = sTsd
        maxSiTort_All_Veins = sTmax

        meanCuTort_All_Veins = cTmean
        sdCuTort_All_Veins = cTsd
        maxCuTort_All_Veins = cTmax

        #[DEPTH]
        strahlerSK, outSK, maxDepth, checkSum = getStrahlerSkeleton(skeletonFull, subMask)
        # ----------------------------------------------------------------------
        # strahlerSkeleton_All_Veins = strahlerSK
        # residualStrahlerSkeleton_All_Veins = outSK

        maxDepth_All_Veins = maxDepth
        residualState_All_Veins = checkSum
        #endregion

        #region ============= ZONE C | COMBINED  =============
        zoneName = "All"
        vesselsMode = arteries | veins         
        
        skeletonFull = skimage.morphology.skeletonize(vesselsMode)
        maskFull, subImage, subMask, wprT, vzrT, wprN, vzrN, wprE, vzrE, wprS, vzrS, wprW, vzrW = getZone(vesselsMode, od, zoneName)
        subSkeleton = numpy.where(subMask!=0, skeletonFull, 0)
        # ----------------------------------------------------------------------

        #[CALIBERS]
        avrBigXCaliberFC_All_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFC_All_Arteries, meanBigXCaliberFC_All_Veins)
        avrBigXCaliberFull_All_AV = getMeanBigXCaliberAVRatio(meanBigXCaliberFull_All_Arteries, meanBigXCaliberFull_All_Veins)

        #[QUANTITY]
        nbOverlapP_All_AV = getNbOverlapPointsCCs(subSkeleton, crossPImg_Arteries, crossPImg_Veins)        
        #endregion

###############################################################

        tmpDict = {
            "image":imageName,\
            
            "wprT_A_Arteries":wprT_A_Arteries,\
            "wprN_A_Arteries":wprN_A_Arteries,\
            "wprE_A_Arteries":wprE_A_Arteries,\
            "wprS_A_Arteries":wprS_A_Arteries,\
            "wprW_A_Arteries":wprW_A_Arteries,\
            "vzrT_A_Arteries":vzrT_A_Arteries,\
            "vzrN_A_Arteries":vzrN_A_Arteries,\
            "vzrE_A_Arteries":vzrE_A_Arteries,\
            "vzrS_A_Arteries":vzrS_A_Arteries,\
            "vzrW_A_Arteries":vzrW_A_Arteries,\
            "meanCaliberFC_A_Arteries":meanCaliberFC_A_Arteries,\
            "sdCaliberFC_A_Arteries":sdCaliberFC_A_Arteries,\
            "meanBigXCaliberFC_A_Arteries":meanBigXCaliberFC_A_Arteries,\
            "sdBigXCaliberFC_A_Arteries":sdBigXCaliberFC_A_Arteries,\
            "nbXFC_A_Arteries":nbXFC_A_Arteries,\
            "meanCaliberFull_A_Arteries":meanCaliberFull_A_Arteries,\
            "sdCaliberFull_A_Arteries":sdCaliberFull_A_Arteries,\
            "meanBigXCaliberFull_A_Arteries":meanBigXCaliberFull_A_Arteries,\
            "sdBigXCaliberFull_A_Arteries":sdBigXCaliberFull_A_Arteries,\
            "nbXFull_A_Arteries":nbXFull_A_Arteries,\
            "fractalDim_A_Arteries":fractalDim_A_Arteries,\
            "nbCC_A_Arteries":nbCC_A_Arteries,\
            "area_A_Arteries":area_A_Arteries,\
            "areaSkeleton_A_Arteries":areaSkeleton_A_Arteries,\
            "nbEndP_A_Arteries":nbEndP_A_Arteries,\
            "nbCrossP_A_Arteries":nbCrossP_A_Arteries,\

            "wprT_A_Veins":wprT_A_Veins,\
            "wprN_A_Veins":wprN_A_Veins,\
            "wprE_A_Veins":wprE_A_Veins,\
            "wprS_A_Veins":wprS_A_Veins,\
            "wprW_A_Veins":wprW_A_Veins,\
            "vzrT_A_Veins":vzrT_A_Veins,\
            "vzrN_A_Veins":vzrN_A_Veins,\
            "vzrE_A_Veins":vzrE_A_Veins,\
            "vzrS_A_Veins":vzrS_A_Veins,\
            "vzrW_A_Veins":vzrW_A_Veins,\
            "meanCaliberFC_A_Veins":meanCaliberFC_A_Veins,\
            "sdCaliberFC_A_Veins":sdCaliberFC_A_Veins,\
            "meanBigXCaliberFC_A_Veins":meanBigXCaliberFC_A_Veins,\
            "sdBigXCaliberFC_A_Veins":sdBigXCaliberFC_A_Veins,\
            "nbXFC_A_Veins":nbXFC_A_Veins,\
            "meanCaliberFull_A_Veins":meanCaliberFull_A_Veins,\
            "sdCaliberFull_A_Veins":sdCaliberFull_A_Veins,\
            "meanBigXCaliberFull_A_Veins":meanBigXCaliberFull_A_Veins,\
            "sdBigXCaliberFull_A_Veins":sdBigXCaliberFull_A_Veins,\
            "nbXFull_A_Veins":nbXFull_A_Veins,\
            "fractalDim_A_Veins":fractalDim_A_Veins,\
            "nbCC_A_Veins":nbCC_A_Veins,\
            "area_A_Veins":area_A_Veins,\
            "areaSkeleton_A_Veins":areaSkeleton_A_Veins,\
            "nbEndP_A_Veins":nbEndP_A_Veins,\
            "nbCrossP_A_Veins":nbCrossP_A_Veins,\
              
            "avrBigXCaliberFC_A_AV":avrBigXCaliberFC_A_AV,\
            "avrBigXCaliberFull_A_AV":avrBigXCaliberFull_A_AV,\
            "nbOverlapP_A_AV":nbOverlapP_A_AV,\
            

            
            "wprT_B_Arteries":wprT_B_Arteries,\
            "wprN_B_Arteries":wprN_B_Arteries,\
            "wprE_B_Arteries":wprE_B_Arteries,\
            "wprS_B_Arteries":wprS_B_Arteries,\
            "wprW_B_Arteries":wprW_B_Arteries,\
            "vzrT_B_Arteries":vzrT_B_Arteries,\
            "vzrN_B_Arteries":vzrN_B_Arteries,\
            "vzrE_B_Arteries":vzrE_B_Arteries,\
            "vzrS_B_Arteries":vzrS_B_Arteries,\
            "vzrW_B_Arteries":vzrW_B_Arteries,\
            "meanCaliberFC_B_Arteries":meanCaliberFC_B_Arteries,\
            "sdCaliberFC_B_Arteries":sdCaliberFC_B_Arteries,\
            "meanBigXCaliberFC_B_Arteries":meanBigXCaliberFC_B_Arteries,\
            "sdBigXCaliberFC_B_Arteries":sdBigXCaliberFC_B_Arteries,\
            "nbXFC_B_Arteries":nbXFC_B_Arteries,\
            "meanCaliberFull_B_Arteries":meanCaliberFull_B_Arteries,\
            "sdCaliberFull_B_Arteries":sdCaliberFull_B_Arteries,\
            "meanBigXCaliberFull_B_Arteries":meanBigXCaliberFull_B_Arteries,\
            "sdBigXCaliberFull_B_Arteries":sdBigXCaliberFull_B_Arteries,\
            "nbXFull_B_Arteries":nbXFull_B_Arteries,\
            "fractalDim_B_Arteries":fractalDim_B_Arteries,\
            "nbCC_B_Arteries":nbCC_B_Arteries,\
            "area_B_Arteries":area_B_Arteries,\
            "areaSkeleton_B_Arteries":areaSkeleton_B_Arteries,\
            "nbEndP_B_Arteries":nbEndP_B_Arteries,\
            "nbCrossP_B_Arteries":nbCrossP_B_Arteries,\

            "wprT_B_Veins":wprT_B_Veins,\
            "wprN_B_Veins":wprN_B_Veins,\
            "wprE_B_Veins":wprE_B_Veins,\
            "wprS_B_Veins":wprS_B_Veins,\
            "wprW_B_Veins":wprW_B_Veins,\
            "vzrT_B_Veins":vzrT_B_Veins,\
            "vzrN_B_Veins":vzrN_B_Veins,\
            "vzrE_B_Veins":vzrE_B_Veins,\
            "vzrS_B_Veins":vzrS_B_Veins,\
            "vzrW_B_Veins":vzrW_B_Veins,\
            "meanCaliberFC_B_Veins":meanCaliberFC_B_Veins,\
            "sdCaliberFC_B_Veins":sdCaliberFC_B_Veins,\
            "meanBigXCaliberFC_B_Veins":meanBigXCaliberFC_B_Veins,\
            "sdBigXCaliberFC_B_Veins":sdBigXCaliberFC_B_Veins,\
            "nbXFC_B_Veins":nbXFC_B_Veins,\
            "meanCaliberFull_B_Veins":meanCaliberFull_B_Veins,\
            "sdCaliberFull_B_Veins":sdCaliberFull_B_Veins,\
            "meanBigXCaliberFull_B_Veins":meanBigXCaliberFull_B_Veins,\
            "sdBigXCaliberFull_B_Veins":sdBigXCaliberFull_B_Veins,\
            "nbXFull_B_Veins":nbXFull_B_Veins,\
            "fractalDim_B_Veins":fractalDim_B_Veins,\
            "nbCC_B_Veins":nbCC_B_Veins,\
            "area_B_Veins":area_B_Veins,\
            "areaSkeleton_B_Veins":areaSkeleton_B_Veins,\
            "nbEndP_B_Veins":nbEndP_B_Veins,\
            "nbCrossP_B_Veins":nbCrossP_B_Veins,\
              
            "avrBigXCaliberFC_B_AV":avrBigXCaliberFC_B_AV,\
            "avrBigXCaliberFull_B_AV":avrBigXCaliberFull_B_AV,\
            "nbOverlapP_B_AV":nbOverlapP_B_AV,\
            

            
            "wprT_C_Arteries":wprT_C_Arteries,\
            "wprN_C_Arteries":wprN_C_Arteries,\
            "wprE_C_Arteries":wprE_C_Arteries,\
            "wprS_C_Arteries":wprS_C_Arteries,\
            "wprW_C_Arteries":wprW_C_Arteries,\
            "vzrT_C_Arteries":vzrT_C_Arteries,\
            "vzrN_C_Arteries":vzrN_C_Arteries,\
            "vzrE_C_Arteries":vzrE_C_Arteries,\
            "vzrS_C_Arteries":vzrS_C_Arteries,\
            "vzrW_C_Arteries":vzrW_C_Arteries,\
            "meanCaliberFC_C_Arteries":meanCaliberFC_C_Arteries,\
            "sdCaliberFC_C_Arteries":sdCaliberFC_C_Arteries,\
            "meanBigXCaliberFC_C_Arteries":meanBigXCaliberFC_C_Arteries,\
            "sdBigXCaliberFC_C_Arteries":sdBigXCaliberFC_C_Arteries,\
            "nbXFC_C_Arteries":nbXFC_C_Arteries,\
            "meanCaliberFull_C_Arteries":meanCaliberFull_C_Arteries,\
            "sdCaliberFull_C_Arteries":sdCaliberFull_C_Arteries,\
            "meanBigXCaliberFull_C_Arteries":meanBigXCaliberFull_C_Arteries,\
            "sdBigXCaliberFull_C_Arteries":sdBigXCaliberFull_C_Arteries,\
            "nbXFull_C_Arteries":nbXFull_C_Arteries,\
            "fractalDim_C_Arteries":fractalDim_C_Arteries,\
            "nbCC_C_Arteries":nbCC_C_Arteries,\
            "area_C_Arteries":area_C_Arteries,\
            "areaSkeleton_C_Arteries":areaSkeleton_C_Arteries,\
            "nbEndP_C_Arteries":nbEndP_C_Arteries,\
            "nbCrossP_C_Arteries":nbCrossP_C_Arteries,\

            "wprT_C_Veins":wprT_C_Veins,\
            "wprN_C_Veins":wprN_C_Veins,\
            "wprE_C_Veins":wprE_C_Veins,\
            "wprS_C_Veins":wprS_C_Veins,\
            "wprW_C_Veins":wprW_C_Veins,\
            "vzrT_C_Veins":vzrT_C_Veins,\
            "vzrN_C_Veins":vzrN_C_Veins,\
            "vzrE_C_Veins":vzrE_C_Veins,\
            "vzrS_C_Veins":vzrS_C_Veins,\
            "vzrW_C_Veins":vzrW_C_Veins,\
            "meanCaliberFC_C_Veins":meanCaliberFC_C_Veins,\
            "sdCaliberFC_C_Veins":sdCaliberFC_C_Veins,\
            "meanBigXCaliberFC_C_Veins":meanBigXCaliberFC_C_Veins,\
            "sdBigXCaliberFC_C_Veins":sdBigXCaliberFC_C_Veins,\
            "nbXFC_C_Veins":nbXFC_C_Veins,\
            "meanCaliberFull_C_Veins":meanCaliberFull_C_Veins,\
            "sdCaliberFull_C_Veins":sdCaliberFull_C_Veins,\
            "meanBigXCaliberFull_C_Veins":meanBigXCaliberFull_C_Veins,\
            "sdBigXCaliberFull_C_Veins":sdBigXCaliberFull_C_Veins,\
            "nbXFull_C_Veins":nbXFull_C_Veins,\
            "fractalDim_C_Veins":fractalDim_C_Veins,\
            "nbCC_C_Veins":nbCC_C_Veins,\
            "area_C_Veins":area_C_Veins,\
            "areaSkeleton_C_Veins":areaSkeleton_C_Veins,\
            "nbEndP_C_Veins":nbEndP_C_Veins,\
            "nbCrossP_C_Veins":nbCrossP_C_Veins,\
              
            "avrBigXCaliberFC_C_AV":avrBigXCaliberFC_C_AV,\
            "avrBigXCaliberFull_C_AV":avrBigXCaliberFull_C_AV,\
            "nbOverlapP_C_AV":nbOverlapP_C_AV,\
            

            
            "wprT_Out_Arteries":wprT_Out_Arteries,\
            "wprN_Out_Arteries":wprN_Out_Arteries,\
            "wprE_Out_Arteries":wprE_Out_Arteries,\
            "wprS_Out_Arteries":wprS_Out_Arteries,\
            "wprW_Out_Arteries":wprW_Out_Arteries,\
            "vzrT_Out_Arteries":vzrT_Out_Arteries,\
            "vzrN_Out_Arteries":vzrN_Out_Arteries,\
            "vzrE_Out_Arteries":vzrE_Out_Arteries,\
            "vzrS_Out_Arteries":vzrS_Out_Arteries,\
            "vzrW_Out_Arteries":vzrW_Out_Arteries,\
            "meanCaliberFC_Out_Arteries":meanCaliberFC_Out_Arteries,\
            "sdCaliberFC_Out_Arteries":sdCaliberFC_Out_Arteries,\
            "meanBigXCaliberFC_Out_Arteries":meanBigXCaliberFC_Out_Arteries,\
            "sdBigXCaliberFC_Out_Arteries":sdBigXCaliberFC_Out_Arteries,\
            "nbXFC_Out_Arteries":nbXFC_Out_Arteries,\
            "meanCaliberFull_Out_Arteries":meanCaliberFull_Out_Arteries,\
            "sdCaliberFull_Out_Arteries":sdCaliberFull_Out_Arteries,\
            "meanBigXCaliberFull_Out_Arteries":meanBigXCaliberFull_Out_Arteries,\
            "sdBigXCaliberFull_Out_Arteries":sdBigXCaliberFull_Out_Arteries,\
            "nbXFull_Out_Arteries":nbXFull_Out_Arteries,\
            "fractalDim_Out_Arteries":fractalDim_Out_Arteries,\
            "nbCC_Out_Arteries":nbCC_Out_Arteries,\
            "area_Out_Arteries":area_Out_Arteries,\
            "areaSkeleton_Out_Arteries":areaSkeleton_Out_Arteries,\
            "nbEndP_Out_Arteries":nbEndP_Out_Arteries,\
            "nbCrossP_Out_Arteries":nbCrossP_Out_Arteries,\

            "wprT_Out_Veins":wprT_Out_Veins,\
            "wprN_Out_Veins":wprN_Out_Veins,\
            "wprE_Out_Veins":wprE_Out_Veins,\
            "wprS_Out_Veins":wprS_Out_Veins,\
            "wprW_Out_Veins":wprW_Out_Veins,\
            "vzrT_Out_Veins":vzrT_Out_Veins,\
            "vzrN_Out_Veins":vzrN_Out_Veins,\
            "vzrE_Out_Veins":vzrE_Out_Veins,\
            "vzrS_Out_Veins":vzrS_Out_Veins,\
            "vzrW_Out_Veins":vzrW_Out_Veins,\
            "meanCaliberFC_Out_Veins":meanCaliberFC_Out_Veins,\
            "sdCaliberFC_Out_Veins":sdCaliberFC_Out_Veins,\
            "meanBigXCaliberFC_Out_Veins":meanBigXCaliberFC_Out_Veins,\
            "sdBigXCaliberFC_Out_Veins":sdBigXCaliberFC_Out_Veins,\
            "nbXFC_Out_Veins":nbXFC_Out_Veins,\
            "meanCaliberFull_Out_Veins":meanCaliberFull_Out_Veins,\
            "sdCaliberFull_Out_Veins":sdCaliberFull_Out_Veins,\
            "meanBigXCaliberFull_Out_Veins":meanBigXCaliberFull_Out_Veins,\
            "sdBigXCaliberFull_Out_Veins":sdBigXCaliberFull_Out_Veins,\
            "nbXFull_Out_Veins":nbXFull_Out_Veins,\
            "fractalDim_Out_Veins":fractalDim_Out_Veins,\
            "nbCC_Out_Veins":nbCC_Out_Veins,\
            "area_Out_Veins":area_Out_Veins,\
            "areaSkeleton_Out_Veins":areaSkeleton_Out_Veins,\
            "nbEndP_Out_Veins":nbEndP_Out_Veins,\
            "nbCrossP_Out_Veins":nbCrossP_Out_Veins,\
              
            "avrBigXCaliberFC_Out_AV":avrBigXCaliberFC_Out_AV,\
            "avrBigXCaliberFull_Out_AV":avrBigXCaliberFull_Out_AV,\
            "nbOverlapP_Out_AV":nbOverlapP_Out_AV,\
            

            
            "wprT_All_Arteries":wprT_All_Arteries,\
            "wprN_All_Arteries":wprN_All_Arteries,\
            "wprE_All_Arteries":wprE_All_Arteries,\
            "wprS_All_Arteries":wprS_All_Arteries,\
            "wprW_All_Arteries":wprW_All_Arteries,\
            "vzrT_All_Arteries":vzrT_All_Arteries,\
            "vzrN_All_Arteries":vzrN_All_Arteries,\
            "vzrE_All_Arteries":vzrE_All_Arteries,\
            "vzrS_All_Arteries":vzrS_All_Arteries,\
            "vzrW_All_Arteries":vzrW_All_Arteries,\
            "meanCaliberFC_All_Arteries":meanCaliberFC_All_Arteries,\
            "sdCaliberFC_All_Arteries":sdCaliberFC_All_Arteries,\
            "meanBigXCaliberFC_All_Arteries":meanBigXCaliberFC_All_Arteries,\
            "sdBigXCaliberFC_All_Arteries":sdBigXCaliberFC_All_Arteries,\
            "nbXFC_All_Arteries":nbXFC_All_Arteries,\
            "meanCaliberFull_All_Arteries":meanCaliberFull_All_Arteries,\
            "sdCaliberFull_All_Arteries":sdCaliberFull_All_Arteries,\
            "meanBigXCaliberFull_All_Arteries":meanBigXCaliberFull_All_Arteries,\
            "sdBigXCaliberFull_All_Arteries":sdBigXCaliberFull_All_Arteries,\
            "nbXFull_All_Arteries":nbXFull_All_Arteries,\
            "fractalDim_All_Arteries":fractalDim_All_Arteries,\
            "nbCC_All_Arteries":nbCC_All_Arteries,\
            "area_All_Arteries":area_All_Arteries,\
            "areaSkeleton_All_Arteries":areaSkeleton_All_Arteries,\
            "nbEndP_All_Arteries":nbEndP_All_Arteries,\
            "nbCrossP_All_Arteries":nbCrossP_All_Arteries,\
            "meanSiTort_All_Arteries":meanSiTort_All_Arteries,\
            "sdSiTort_All_Arteries":sdSiTort_All_Arteries,\
            "maxSiTort_All_Arteries":maxSiTort_All_Arteries,\
            "meanCuTort_All_Arteries":meanCuTort_All_Arteries,\
            "sdCuTort_All_Arteries":sdCuTort_All_Arteries,\
            "maxCuTort_All_Arteries":maxCuTort_All_Arteries,\
            "maxDepth_All_Arteries":maxDepth_All_Arteries,\
            "residualState_All_Arteries":residualState_All_Arteries,\

            "wprT_All_Veins":wprT_All_Veins,\
            "wprN_All_Veins":wprN_All_Veins,\
            "wprE_All_Veins":wprE_All_Veins,\
            "wprS_All_Veins":wprS_All_Veins,\
            "wprW_All_Veins":wprW_All_Veins,\
            "vzrT_All_Veins":vzrT_All_Veins,\
            "vzrN_All_Veins":vzrN_All_Veins,\
            "vzrE_All_Veins":vzrE_All_Veins,\
            "vzrS_All_Veins":vzrS_All_Veins,\
            "vzrW_All_Veins":vzrW_All_Veins,\
            "meanCaliberFC_All_Veins":meanCaliberFC_All_Veins,\
            "sdCaliberFC_All_Veins":sdCaliberFC_All_Veins,\
            "meanBigXCaliberFC_All_Veins":meanBigXCaliberFC_All_Veins,\
            "sdBigXCaliberFC_All_Veins":sdBigXCaliberFC_All_Veins,\
            "nbXFC_All_Veins":nbXFC_All_Veins,\
            "meanCaliberFull_All_Veins":meanCaliberFull_All_Veins,\
            "sdCaliberFull_All_Veins":sdCaliberFull_All_Veins,\
            "meanBigXCaliberFull_All_Veins":meanBigXCaliberFull_All_Veins,\
            "sdBigXCaliberFull_All_Veins":sdBigXCaliberFull_All_Veins,\
            "nbXFull_All_Veins":nbXFull_All_Veins,\
            "fractalDim_All_Veins":fractalDim_All_Veins,\
            "nbCC_All_Veins":nbCC_All_Veins,\
            "area_All_Veins":area_All_Veins,\
            "areaSkeleton_All_Veins":areaSkeleton_All_Veins,\
            "nbEndP_All_Veins":nbEndP_All_Veins,\
            "nbCrossP_All_Veins":nbCrossP_All_Veins,\
            "meanSiTort_All_Veins":meanSiTort_All_Veins,\
            "sdSiTort_All_Veins":sdSiTort_All_Veins,\
            "maxSiTort_All_Veins":maxSiTort_All_Veins,\
            "meanCuTort_All_Veins":meanCuTort_All_Veins,\
            "sdCuTort_All_Veins":sdCuTort_All_Veins,\
            "maxCuTort_All_Veins":maxCuTort_All_Veins,\
            "maxDepth_All_Veins":maxDepth_All_Veins,\
            "residualState_All_Veins":residualState_All_Veins,\
            
            "avrBigXCaliberFC_All_AV":avrBigXCaliberFC_All_AV,\
            "avrBigXCaliberFull_All_AV":avrBigXCaliberFull_All_AV,\
            "nbOverlapP_All_AV":nbOverlapP_All_AV,\
            
        }
        measuresDict[imageName] = tmpDict

    exportToCSV(measuresDict, writeFile)

if __name__ == '__main__':
    main(sys.argv)

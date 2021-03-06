#!/usr/bin/env python

## Program:   VMTK
## Module:    $RCSfile: vmtkimagefeatures.py,v $
## Language:  Python
## Date:      $Date: 2006/07/17 09:53:14 $
## Version:   $Revision: 1.8 $

##   Copyright (c) Luca Antiga, David Steinman. All rights reserved.
##   See LICENCE file for details.

##      This software is distributed WITHOUT ANY WARRANTY; without even 
##      the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
##      PURPOSE.  See the above copyright notices for more information.


import vtk
import sys

import pypes
import vtkvmtk

vmtkimagefeatures = 'vmtkImageFeatures'

class vmtkImageFeatures(pypes.pypeScript):

    def __init__(self):

        pypes.pypeScript.__init__(self)
        
        self.Image = None
        self.FeatureImage = None
  
        self.Dimensionality = 3

        self.DerivativeSigma = 0.0
        self.SigmoidRemapping = 0
        self.FeatureImageType = 'gradient'
        self.UpwindFactor = 1.0

        self.FWHMRadius = [3, 3, 3]
        self.FWHMBackgroundValue = 0.0

        self.SetScriptName('vmtkimagefeatures')
        self.SetScriptDoc('compute a feature image for use in segmentation')
        self.SetInputMembers([
            ['Image','i','vtkImageData',1,'','the input image','vmtkimagereader'],
            ['FeatureImageType','featureimagetype','str',1,'["vtkgradient","gradient","upwind","fwhm"]'],
            ['Dimensionality','dimensionality','int',1,'(2,3,1)'],
            ['SigmoidRemapping','sigmoid','bool',1],
            ['DerivativeSigma','derivativesigma','float',1,'(0.0,)'],
            ['UpwindFactor','upwindfactor','float',1,'(0.0,1.0)'],
            ['FWHMRadius','fwhmradius','int',3,'(0,)'],
            ['FWHMBackgroundValue','fwhmbackgroundvalue','float',1]
            ])
        self.SetOutputMembers([
            ['Image','o','vtkImageData',1,'','the output image','vmtkimagewriter']
            ])
    
    def BuildVTKGradientBasedFeatureImage(self):

        cast = vtk.vtkImageCast()
        cast.SetInput(self.Image)
        cast.SetOutputScalarTypeToFloat()
        cast.Update()

        gradientMagnitude = vtk.vtkImageGradientMagnitude()
        gradientMagnitude.SetInput(cast.GetOutput())
        gradientMagnitude.SetDimensionality(self.Dimensionality)
        gradientMagnitude.Update()

        imageAdd = vtk.vtkImageMathematics()
        imageAdd.SetInput(gradientMagnitude.GetOutput())
        imageAdd.SetOperationToAddConstant()
        imageAdd.SetConstantC(1.0)
        imageAdd.Update()

        imageInvert = vtk.vtkImageMathematics()
        imageInvert.SetInput(imageAdd.GetOutput())
        imageInvert.SetOperationToInvert()
        imageInvert.SetConstantC(1E20)
        imageInvert.DivideByZeroToCOn()
        imageInvert.Update()

        self.FeatureImage = vtk.vtkImageData()
        self.FeatureImage.DeepCopy(imageInvert.GetOutput())
        self.FeatureImage.Update()

    def BuildFWHMBasedFeatureImage(self):
        
        cast = vtk.vtkImageCast()
        cast.SetInput(self.Image)
        cast.SetOutputScalarTypeToFloat()
        cast.Update()

        fwhmFeatureImageFilter = vtkvmtk.vtkvmtkFWHMFeatureImageFilter()
        fwhmFeatureImageFilter.SetInput(cast.GetOutput())
        fwhmFeatureImageFilter.SetRadius(self.FWHMRadius)
        fwhmFeatureImageFilter.SetBackgroundValue(self.FWHMBackgroundValue)
        fwhmFeatureImageFilter.Update()
	
        self.FeatureImage = vtk.vtkImageData()
        self.FeatureImage.DeepCopy(fwhmFeatureImageFilter.GetOutput())
        self.FeatureImage.Update()

    def BuildUpwindGradientBasedFeatureImage(self):
 
        cast = vtk.vtkImageCast()
        cast.SetInput(self.Image)
        cast.SetOutputScalarTypeToFloat()
        cast.Update()
       
        gradientMagnitude = vtkvmtk.vtkvmtkUpwindGradientMagnitudeImageFilter()
        gradientMagnitude.SetInput(cast.GetOutput())
        gradientMagnitude.SetUpwindFactor(self.UpwindFactor)
        gradientMagnitude.Update()

        featureImage = None
        if self.SigmoidRemapping==1:
            scalarRange = gradientMagnitude.GetOutput().GetPointData().GetScalars().GetRange()
            inputMinimum = scalarRange[0]
            inputMaximum = scalarRange[1]
            alpha = - (inputMaximum - inputMinimum) / 6.0
            beta = (inputMaximum + inputMinimum) / 2.0
            sigmoid = vtkvmtk.vtkvmtkSigmoidImageFilter()
            sigmoid.SetInput(gradientMagnitude.GetOutput())
            sigmoid.SetAlpha(alpha)
            sigmoid.SetBeta(beta)
            sigmoid.SetOutputMinimum(0.0)
            sigmoid.SetOutputMaximum(1.0)
            sigmoid.Update()
            featureImage = sigmoid.GetOutput()
        else:
            boundedReciprocal = vtkvmtk.vtkvmtkBoundedReciprocalImageFilter()
            boundedReciprocal.SetInput(gradientMagnitude.GetOutput())
            boundedReciprocal.Update()
            featureImage = boundedReciprocal.GetOutput()
 
        self.FeatureImage = vtk.vtkImageData()
        self.FeatureImage.DeepCopy(featureImage)
        self.FeatureImage.Update()
  
    def BuildGradientBasedFeatureImage(self):

        cast = vtk.vtkImageCast()
        cast.SetInput(self.Image)
        cast.SetOutputScalarTypeToFloat()
        cast.Update()

        if (self.DerivativeSigma > 0.0):
            gradientMagnitude = vtkvmtk.vtkvmtkGradientMagnitudeRecursiveGaussianImageFilter()
            gradientMagnitude.SetInput(cast.GetOutput())
            gradientMagnitude.SetSigma(self.DerivativeSigma)
            gradientMagnitude.SetNormalizeAcrossScale(0)
            gradientMagnitude.Update()
        else:
            gradientMagnitude = vtkvmtk.vtkvmtkGradientMagnitudeImageFilter()
            gradientMagnitude.SetInput(cast.GetOutput())
            gradientMagnitude.Update()

        featureImage = None
        if self.SigmoidRemapping==1:
            scalarRange = gradientMagnitude.GetOutput().GetPointData().GetScalars().GetRange()
            inputMinimum = scalarRange[0]
            inputMaximum = scalarRange[1]
            alpha = - (inputMaximum - inputMinimum) / 6.0
            beta = (inputMaximum + inputMinimum) / 2.0
            sigmoid = vtkvmtk.vtkvmtkSigmoidImageFilter()
            sigmoid.SetInput(gradientMagnitude.GetOutput())
            sigmoid.SetAlpha(alpha)
            sigmoid.SetBeta(beta)
            sigmoid.SetOutputMinimum(0.0)
            sigmoid.SetOutputMaximum(1.0)
            sigmoid.Update()
            featureImage = sigmoid.GetOutput()
        else:
            boundedReciprocal = vtkvmtk.vtkvmtkBoundedReciprocalImageFilter()
            boundedReciprocal.SetInput(gradientMagnitude.GetOutput())
            boundedReciprocal.Update()
            featureImage = boundedReciprocal.GetOutput()

        self.FeatureImage = vtk.vtkImageData()
        self.FeatureImage.DeepCopy(featureImage)
        self.FeatureImage.Update()

    def Execute(self):

        if self.Image == None:
            self.PrintError('Error: No input image.')

        if self.FeatureImageType == 'vtkgradient':
          self.BuildVTKGradientBasedFeatureImage()
        elif self.FeatureImageType == 'gradient':
          self.BuildGradientBasedFeatureImage()
        elif self.FeatureImageType == 'upwind':
          self.BuildUpwindGradientBasedFeatureImage()
        elif self.FeatureImageType == 'fwhm':
          self.BuildFWHMBasedFeatureImage()
        else:
          self.PrintError('Error: unsupported feature image type')

        self.Image = self.FeatureImage


if __name__=='__main__':

    main = pypes.pypeMain()
    main.Arguments = sys.argv
    main.Execute()

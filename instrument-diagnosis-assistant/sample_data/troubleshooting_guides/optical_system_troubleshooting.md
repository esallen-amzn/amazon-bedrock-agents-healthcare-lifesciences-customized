# Optical System Troubleshooting Guide

## Overview
This guide covers common optical system issues in the XYZ-2000 instrument, including laser power problems, detection issues, and signal quality degradation.

## Laser Power Issues

### Symptom: Low Laser Power (Below 80%)
**Indicators in Logs:**
- "Laser power: XX% (Below threshold)" where XX < 80
- "Signal too weak" errors during analysis
- "Retry Attempt X: FAILED - Laser power insufficient"

**Troubleshooting Steps:**
1. **Check Power Supply**
   - Verify main power connection is secure
   - Check power supply voltage: should be 24V ±0.5V
   - Look for power supply error LEDs

2. **Inspect Laser Module**
   - Visual inspection for damage or contamination
   - Check laser module temperature (should be <40°C)
   - Verify cooling fan operation

3. **Clean Optical Path**
   - Power down system completely
   - Remove optical access panel (see diagram below)
   - Clean laser output window with lint-free cloth and isopropanol
   - Clean beam path mirrors and lenses

4. **Calibrate Laser Power**
   - Access Service Menu → Optical Calibration
   - Run laser power calibration routine
   - If calibration fails, laser module may need replacement

**Expected Results:**
- Laser power should return to 85-95% range
- System logs should show "Laser power: XX%" where XX ≥ 80
- Analysis should proceed without power-related errors

## Detection Array Problems

### Symptom: Poor Signal Quality (SNR < 20 dB)
**Indicators in Logs:**
- "Signal Processing: ABORTED - SNR: XX dB (Below threshold)" where XX < 20
- "Data Validation: FAIL - Quality score: XX%" where XX < 70
- "Channel dropout" or "sensitivity degradation" warnings

**Troubleshooting Steps:**
1. **Check Detector Alignment**
   - Access Alignment Menu in service mode
   - Run detector alignment check
   - Adjust if alignment error > 0.1mm

2. **Clean Detection Optics**
   - Remove detector housing cover
   - Clean detector windows with appropriate cleaning solution
   - Check for dust or contamination on optical surfaces

3. **Verify Electronic Connections**
   - Check all detector cable connections
   - Look for loose or corroded connectors
   - Verify detector power supply voltages

4. **Run Detector Calibration**
   - Service Menu → Detector Calibration
   - Use reference standards for calibration
   - Replace detectors if calibration fails

## Temperature Control Issues

### Symptom: Temperature Instability (±0.5°C or greater)
**Indicators in Logs:**
- "Temperature Control: UNSTABLE - XX°C ±YY°C (Out of range)"
- "Temperature drift detected"
- "Thermal drift" errors during analysis

**Troubleshooting Steps:**
1. **Check Cooling System**
   - Verify cooling fan operation (should be audible)
   - Check air intake filters for blockage
   - Ensure adequate ventilation around instrument

2. **Inspect Temperature Sensors**
   - Check sensor cable connections
   - Verify sensor readings in diagnostic mode
   - Replace sensors if readings are inconsistent

3. **Calibrate Temperature Control**
   - Access Service Menu → Temperature Calibration
   - Allow 30 minutes for thermal equilibration
   - Run calibration with external reference thermometer

**Safety Notes:**
- Always power down before opening optical compartments
- Use appropriate ESD protection when handling electronic components
- Refer to service manual for detailed component locations

## Visual Reference Diagrams

### Optical Module Layout
```
    Laser ──→ Mirror 1 ──→ Sample Cell ──→ Mirror 2 ──→ Detector Array
      │                        │                           │
      ▼                        ▼                           ▼
  Power Monitor          Temperature         Signal Processing
                          Sensor                  Unit
```

### Access Panel Locations
- **Optical Access Panel**: Front right side, 4 screws
- **Detector Housing**: Top panel, slide-out design  
- **Temperature Sensor**: Left side panel, behind filter

## Preventive Maintenance

### Weekly Checks
- Visual inspection of optical windows
- Check cooling fan operation
- Verify temperature stability

### Monthly Maintenance  
- Clean optical surfaces
- Check all cable connections
- Run system performance check

### Quarterly Service
- Full optical alignment check
- Replace air filters
- Comprehensive calibration verification

## When to Contact Service
Contact technical support if:
- Laser power cannot be restored above 80%
- Multiple detector channels fail calibration
- Temperature control cannot maintain ±0.2°C stability
- Any safety-related issues are observed
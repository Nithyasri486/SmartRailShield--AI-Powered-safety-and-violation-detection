# 🚨 IMPORTANT - Which Apps to Run

## ❌ DON'T RUN THESE (OLD/BROKEN):

### 1. obstacle/app.py ❌
```bash
# DON'T DO THIS:
cd obstacle
python app.py
```
**Why NOT:**
- This is the OLD Flask version
- Has cv2.imshow errors
- No visual interface
- **DEPRECATED - DO NOT USE!**

### 2. Drowsiness/drows.py ❌
- Old version with cv2.imshow
- **DEPRECATED - DO NOT USE!**

### 3. licenceplate_recognisation/license1.py ❌
- Old version with cv2.imshow
- **DEPRECATED - DO NOT USE!**

---

## ✅ RUN THESE (NEW/WORKING):

### Option 1: Dashboard Only (Easiest) ⭐ RECOMMENDED

**Run ONLY this:**
```bash
cd d:\Nithyasri\SmartRailShield
python dashboard_app.py
```

**Then:**
1. Open browser: http://localhost:5000
2. Click on any module card to launch it
3. Dashboard will automatically launch the correct Streamlit versions

**That's it! Don't run anything else manually!**

---

### Option 2: Run All Modules Separately (Advanced)

**If you want all modules running at once:**

**Terminal 1 - Dashboard:**
```bash
cd d:\Nithyasri\SmartRailShield
python dashboard_app.py
```
→ Opens at http://localhost:5000

**Terminal 2 - Fault Detection:**
```bash
cd "d:\Nithyasri\SmartRailShield\fault detection"
streamlit run machine.py --server.port 8502
```
→ Opens at http://localhost:8502

**Terminal 3 - Drowsiness Detection:**
```bash
cd d:\Nithyasri\SmartRailShield\Drowsiness
streamlit run drows_streamlit.py --server.port 8503
```
→ Opens at http://localhost:8503

**Terminal 4 - Obstacle Detection:**
```bash
cd d:\Nithyasri\SmartRailShield\obstacle
streamlit run obstacle_streamlit.py --server.port 8501
```
→ Opens at http://localhost:8501

**Terminal 5 - ANPR:**
```bash
cd d:\Nithyasri\SmartRailShield\licenceplate_recognisation
streamlit run np_streamlit.py --server.port 8504
```
→ Opens at http://localhost:8504

---

## 📋 Correct File Names Reference

| Module | ✅ USE THIS | ❌ DON'T USE |
|--------|-------------|--------------|
| Dashboard | `dashboard_app.py` | - |
| Fault Detection | `fault detection/machine.py` | - |
| Drowsiness | `Drowsiness/drows_streamlit.py` | `Drowsiness/drows.py` |
| Obstacle | `obstacle/obstacle_streamlit.py` | `obstacle/app.py` |
| ANPR | `licenceplate_recognisation/np_streamlit.py` | `licenceplate_recognisation/license1.py` |

---

## 🎯 Quick Start (Tamil):

### மிக எளிமையான வழி:

**1. Dashboard மட்டும் run பண்ணுங்க:**
```bash
cd d:\Nithyasri\SmartRailShield
python dashboard_app.py
```

**2. Browser-ல open பண்ணுங்க:**
http://localhost:5000

**3. எந்த module வேணும்னாலும் click பண்ணுங்க:**
- தானா சரியான version launch ஆகும்
- Streamlit-ல open ஆகும்
- cv2.imshow errors இல்லை!

**அவ்ளோதான்!** 🎉

---

## 🚨 Currently Running Issue:

You have `obstacle/app.py` (OLD Flask version) running on port 5000.

**Stop it:**
```bash
# Press Ctrl+C in the terminal where it's running
```

**Then run the correct dashboard:**
```bash
cd d:\Nithyasri\SmartRailShield
python dashboard_app.py
```

---

## ✅ Key Points:

1. **Always use Streamlit versions** (files ending with `_streamlit.py`)
2. **Dashboard automatically launches correct versions**
3. **Never run `app.py` in obstacle folder** - it's deprecated
4. **All visual modules are Streamlit** - no cv2.imshow!

---

## 🎯 What You Should See:

### Correct Dashboard (dashboard_app.py):
```
============================================
🚆 SMARTRAILSHIELD DASHBOARD
============================================

📊 Dashboard starting...
🌐 Open your browser and navigate to: http://localhost:5000

💡 Click on any module card to launch it
⌨️  Keyboard shortcuts: Ctrl+1, Ctrl+2, Ctrl+3, Ctrl+4
```

### Wrong Flask App (obstacle/app.py): ❌
```
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```
**If you see this, you're running the WRONG app!**

---

## 🔧 How to Fix Right Now:

1. **Press Ctrl+C** in terminal showing "Serving Flask app 'app'"
2. **Run:**
   ```bash
   cd d:\Nithyasri\SmartRailShield
   python dashboard_app.py
   ```
3. **Open:** http://localhost:5000
4. **Click:** "Obstacle Detection" card
5. **Works!** No cv2.imshow errors! ✅

---

**Run the CORRECT dashboard now!** 🚀

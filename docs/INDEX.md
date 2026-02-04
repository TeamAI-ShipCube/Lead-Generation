# Documentation Index

## Quick Navigation

Choose your documentation based on your role and needs:

---

## 🎯 For Everyone

### [README.md](../README.md)
**Start here!** Project overview, features, and quick start.

**Read if you want to:**
- Understand what TestScout does
- See a quick feature list
- Get started in 5 minutes

---

## 👤 For Non-Technical Users

### [USER_GUIDE.md](USER_GUIDE.md)
Complete guide for daily operations.

**Read if you want to:**
- Learn how to start/stop the system
- Edit your target customer descriptions (ICPs)
- View and filter leads in the CSV file
- Understand lead quality scores
- Troubleshoot common issues

**Covers:**
- ✅ What TestScout is (simple explanation)
- ✅ Daily workflow
- ✅ Editing ICPs
- ✅ Understanding results
- ✅ Pro tips for better leads

---

## 🔧 For Technical Users & Developers

### [SETUP.md](SETUP.md)
Step-by-step installation from scratch.

**Read if you want to:**
- Install TestScout on a new machine
- Set up Google Cloud and APIs
- Configure environment variables
- Troubleshoot installation issues

**Covers:**
- ✅ Prerequisites
- ✅ Python environment setup
- ✅ Google Cloud project creation
- ✅ API key generation
- ✅ First test run
- ✅ Common setup problems

---

### [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)
Deep dive into system architecture.

**Read if you want to:**
- Understand how the system works internally
- Modify or extend functionality
- Debug complex issues
- Integrate with other tools
- Optimize performance

**Covers:**
- ✅ System architecture diagram
- ✅ Module documentation (all 10 modules)
- ✅ Data flow explanations
- ✅ API configuration
- ✅ Code examples for extensions
- ✅ Performance optimization
- ✅ Advanced troubleshooting

---

## ❓ For Everyone

### [FAQ.md](FAQ.md)
Answers to common questions.

**Categories:**
- **General Questions** - What is TestScout? Is it legal?
- **Usage Questions** - How many leads? How to adjust?
- **Data Questions** - What fields? Email accuracy?
- **Technical Questions** - What APIs? How much does it cost?
- **Troubleshooting** - Why no leads? Pipeline stopped?
- **Advanced** - CRM integration? A/B testing?
- **Best Practices** - Recommended workflow? Metrics to track?

---

## 🎓 By Use Case

### "I'm new and just want to use it"
1. Read [README.md](../README.md) (5 min)
2. Ask technical person to set up (docs/SETUP.md)
3. Read [USER_GUIDE.md](USER_GUIDE.md) (15 min)
4. Use [FAQ.md](FAQ.md) as reference

---

### "I need to set it up"
1. Read [README.md](../README.md) (5 min)
2. Follow [SETUP.md](SETUP.md) step-by-step (60-90 min)
3. Skim [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) for troubleshooting
4. Bookmark [FAQ.md](FAQ.md) for questions

---

### "I want to customize/extend it"
1. Read [README.md](../README.md) (5 min)
2. Study [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) (30-60 min)
3. Review module code in `zcap/` folder
4. Use FAQ.md → "Advanced Questions" for patterns

---

### "Something broke, I need to fix it"
1. Check [FAQ.md](FAQ.md) → "Troubleshooting Questions"
2. Review error in `logs/run_*.log`
3. Search [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) for error type
4. If stuck, check [SETUP.md](SETUP.md) for configuration issues

---

## 📄 File Structure

```
docs/
├── INDEX.md              (This file)
├── USER_GUIDE.md         Non-technical daily operations
├── TECHNICAL_GUIDE.md    Architecture & development
├── SETUP.md              Installation guide
└── FAQ.md                Common questions

../
├── README.md             Project overview
├── Input_ICP.csv         Your target customers (edit this!)
├── Master_Leads.csv      Collected leads (view this!)
└── zcap/                 Code modules
```

---

## 🔍 Search Tips

**Looking for specific info?**

Use Ctrl+F (or Cmd+F) and search for keywords:

| Looking for... | Search in... | Keyword |
|---------------|-------------|---------|
| How to start system | USER_GUIDE.md | "Starting the System" |
| API setup | SETUP.md | "Step 6: Setup Google" |
| Module details | TECHNICAL_GUIDE.md | Module name |
| Error explanation | FAQ.md | Error message |
| File paths | README.md | "Project Structure" |
| Cost information | FAQ.md | "cost" or "billing" |
| Email accuracy | FAQ.md | "email" |

---

## 📚 Additional Resources

### Not in docs but useful:

**Code comments:**
- Each `zcap/*.py` file has detailed comments
- Read module docstrings for quick reference

**Log files:**
- `logs/run_*.log` - Real execution examples
- See actual API calls and responses

**Configuration files:**
- `.env` - All API keys and settings
- `zcap/config.py` - Configurable parameters

---

## 🆘 Still Stuck?

1. **Check FAQ first** - 90% of questions answered there
2. **Read relevant guide** - USER vs TECHNICAL based on your role
3. **Check logs** - `logs/` folder has detailed error messages
4. **Ask for help** - Provide: error message, steps to reproduce, log excerpt

---

*Choose a document above to get started!*

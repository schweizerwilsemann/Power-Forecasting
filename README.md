# 🚀 PV Power Forecasting System

Hệ thống dự báo năng lượng mặt trời với các tính năng nâng cao và giao diện hiện đại.

## 📁 Cấu trúc Project

```
PV-Power-Forecasting/
├── backend/                    # Backend FastAPI
│   ├── app/                   # Application code
│   │   ├── api/              # API routes & schemas
│   │   ├── application/      # Business logic services
│   │   ├── domain/           # Domain entities & interfaces
│   │   └── infrastructure/   # Data access & external services
│   ├── artifacts/            # Model artifacts
│   ├── run.py               # Main launcher script
│   ├── requirements.txt     # Python dependencies
│   └── README.md           # Backend documentation
├── frontend/                 # Frontend Vue.js
│   ├── src/
│   │   ├── components/      # Vue components
│   │   └── composables/     # Vue composables
│   ├── package.json        # Node.js dependencies
│   └── README.md          # Frontend documentation
├── tests/                   # Test files
│   ├── test_enhanced_features.py  # Main test suite
│   └── README.md          # Test documentation
├── Renewable.csv           # Sample data
├── ENHANCED_FEATURES.md    # Feature documentation
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
python -m app.train_model --data ../Renewable.csv
python run.py --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🧪 Testing

```bash
# Run test suite
python tests/test_enhanced_features.py

# Or from tests directory
cd tests
python test_enhanced_features.py
```

## ✨ Features

### 🎯 Core Features
- **Real-time Forecasting**: Dự báo năng lượng theo thời gian thực
- **Advanced ML Models**: LightGBM + Ensemble models
- **Confidence Intervals**: Khoảng tin cậy cho dự báo
- **Multiple Scenarios**: Dự báo với nhiều kịch bản thời tiết

### 📊 Dashboard & Monitoring
- **System Health**: Giám sát sức khỏe hệ thống
- **Performance Metrics**: CPU, Memory, Disk usage
- **Data Quality**: Đánh giá chất lượng dữ liệu
- **Anomaly Detection**: Phát hiện bất thường

### 🔧 Data Management
- **Import/Export**: CSV, JSON, Excel support
- **Data Validation**: Kiểm tra chất lượng dữ liệu
- **Quality Rules**: Quy tắc validation linh hoạt
- **Real-time Monitoring**: Giám sát theo thời gian thực

## 🛠️ Development

### Backend Development
```bash
cd backend
python run.py --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Running from Project Root
```bash
# Backend
python backend/run.py --reload

# Tests
python tests/test_enhanced_features.py
```

## 📚 Documentation

- [Enhanced Features](ENHANCED_FEATURES.md) - Chi tiết các tính năng nâng cao
- [Backend API](backend/README.md) - API documentation
- [Frontend Guide](frontend/README.md) - Frontend documentation
- [Test Guide](tests/README.md) - Testing documentation

## 🔧 Configuration

### Environment Variables
```bash
# Backend
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
API_LOG_LEVEL=info

# Frontend
VITE_API_URL=http://localhost:8000
```

### Model Configuration
- **Algorithm**: LightGBM + Random Forest (Ensemble)
- **Features**: Weather data + Historical energy + Time features
- **Horizon**: 1-48 steps (15 minutes each)
- **Confidence**: 95% confidence intervals

## 🚨 Troubleshooting

### Common Issues

1. **Backend won't start**
   ```bash
   # Check if port 8000 is available
   netstat -an | findstr :8000
   
   # Try different port
   python backend/run.py --port 8001
   ```

2. **Model not loaded**
   ```bash
   # Train the model first
   cd backend
   python -m app.train_model --data ../Renewable.csv
   ```

3. **Frontend can't connect to backend**
   ```bash
   # Check backend is running
   curl http://localhost:8000/health
   
   # Update frontend config
   # Edit frontend/.env.development
   VITE_API_URL=http://localhost:8000
   ```

4. **Tests failing**
   ```bash
   # Install test dependencies
   pip install requests
   
   # Check backend is running
   python tests/test_enhanced_features.py
   ```

## 📈 Performance

- **Response Time**: < 100ms for single forecasts
- **Throughput**: 100+ requests/second
- **Memory Usage**: < 500MB typical
- **CPU Usage**: < 10% typical

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: See docs/ directory
- **API Reference**: http://localhost:8000/docs

---

**Version**: 2.0.0  
**Last Updated**: 2024  
**Status**: Active Development

document.addEventListener("DOMContentLoaded", () => {
    const chartContainer = document.getElementById("tvchart-container");
    const loadingSpinner = document.getElementById("chart-loading");
    const elNaik = document.getElementById("val-naik");
    const elTurun = document.getElementById("val-turun");
    let currentInterval = "1m";
    let ws = null;
    let lastCandle = null;
    const chart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: chartContainer.clientHeight || 600,
        watermark: {
            visible: false, 
        },
        layout: {
            background: { type: 'solid', color: '#161b22' },
            textColor: '#c9d1d9',
        },
        grid: {
            vertLines: { color: '#30363d' },
            horzLines: { color: '#30363d' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: '#30363d',
            scaleMargins: {
                top: 0.05,
                bottom: 0.4, 
            },
        },
        timeScale: {
            borderColor: '#30363d',
            timeVisible: true,
            secondsVisible: false,
        },
        localization: {
            timeFormatter: (timestamp) => {
                const d = new Date(timestamp * 1000);
                const m = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
                return `${d.getDate().toString().padStart(2,'0')} ${m[d.getMonth()]} '${d.getFullYear().toString().slice(-2)} ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`;
            }
        },
    });
    const resizeObserver = new ResizeObserver(entries => {
        if (entries.length === 0 || entries[0].target !== chartContainer) { return; }
        const newRect = entries[0].contentRect;
        chart.resize(newRect.width, newRect.height);
    });
    resizeObserver.observe(chartContainer);
    const candleSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
    });
    const smaSeries = chart.addLineSeries({ color: '#2962FF', lineWidth: 1.5, title: 'SMA' });
    const emaSeries = chart.addLineSeries({ color: '#FF9800', lineWidth: 1.5, title: 'EMA', visible: false });
    const bbUpper = chart.addLineSeries({ color: 'rgba(33, 150, 243, 0.4)', lineWidth: 1, title: 'BB Up', visible: false });
    const bbMiddle = chart.addLineSeries({ color: 'rgba(33, 150, 243, 0.8)', lineWidth: 1, title: 'BB Mid', visible: false });
    const bbLower = chart.addLineSeries({ color: 'rgba(33, 150, 243, 0.4)', lineWidth: 1, title: 'BB Low', visible: false });
    const rsiSeries = chart.addLineSeries({
        color: '#9C27B0', lineWidth: 1.5, title: 'RSI',
        priceScaleId: 'rsi',
    });
    chart.priceScale('rsi').applyOptions({
        scaleMargins: { top: 0.65, bottom: 0.2 },
        borderColor: '#30363d',
    });
    const macdSeries = chart.addLineSeries({ color: '#2196F3', lineWidth: 1.5, title: 'MACD', priceScaleId: 'macd', visible: false });
    const macdSignal = chart.addLineSeries({ color: '#FF9800', lineWidth: 1.5, title: 'Signal', priceScaleId: 'macd', visible: false });
    const macdHist = chart.addHistogramSeries({ priceScaleId: 'macd', visible: false });
    chart.priceScale('macd').applyOptions({
        scaleMargins: { top: 0.85, bottom: 0 },
        borderColor: '#30363d',
    });
    const toggleMap = {
        'ind-sma': [smaSeries],
        'ind-ema': [emaSeries],
        'ind-bb': [bbUpper, bbMiddle, bbLower],
        'ind-rsi': [rsiSeries],
        'ind-macd': [macdSeries, macdSignal, macdHist]
    };
    let savedStates = {};
    try {
        savedStates = JSON.parse(localStorage.getItem('indicatorStates')) || {};
    } catch (e) {
        console.warn("Could not load indicator states", e);
    }
    document.querySelectorAll('.ind-toggle').forEach(checkbox => {
        const id = checkbox.id;
        if (savedStates[id] !== undefined) {
            checkbox.checked = savedStates[id];
        }
        const seriesList = toggleMap[id];
        seriesList.forEach(s => s.applyOptions({ visible: checkbox.checked }));
        checkbox.addEventListener('change', (e) => {
            const sList = toggleMap[e.target.id];
            sList.forEach(s => s.applyOptions({ visible: e.target.checked }));
            savedStates[e.target.id] = e.target.checked;
            localStorage.setItem('indicatorStates', JSON.stringify(savedStates));
        });
    });
    let currentFetchAbort = null;
    async function loadHistory(interval) {
        if (currentFetchAbort) {
            currentFetchAbort.abort();
        }
        currentFetchAbort = new AbortController();
        const signal = currentFetchAbort.signal;
        loadingSpinner.style.display = "block";
        try {
            const res = await fetch(`https://alicelieselou-xgbcoin-api.hf.space/api/history?interval=${interval}`, { signal });
            if (!res.ok) throw new Error("API returned " + res.status);
            const data = await res.json();
            if (data && data.length > 0) {
                const candleData = [], smaData = [], emaData = [], 
                      bbUp = [], bbMid = [], bbLow = [],
                      rsiData = [], macdData = [], macdSig = [], macdH = [];
                data.forEach(d => {
                    const t = d.time;
                    candleData.push({ time: t, open: d.open, high: d.high, low: d.low, close: d.close });
                    if (d.sma !== undefined) smaData.push({ time: t, value: d.sma });
                    if (d.ema !== undefined) emaData.push({ time: t, value: d.ema });
                    if (d.bb_upper !== undefined) {
                        bbUp.push({ time: t, value: d.bb_upper });
                        bbMid.push({ time: t, value: d.bb_middle });
                        bbLow.push({ time: t, value: d.bb_lower });
                    }
                    if (d.rsi !== undefined) rsiData.push({ time: t, value: d.rsi });
                    if (d.macd !== undefined) {
                        macdData.push({ time: t, value: d.macd });
                        macdSig.push({ time: t, value: d.macd_signal });
                        macdH.push({ 
                            time: t, 
                            value: d.macd_histogram, 
                            color: d.macd_histogram > 0 ? '#26a69a' : '#ef5350' 
                        });
                    }
                });
                candleSeries.setData(candleData);
                lastCandle = candleData[candleData.length - 1];
                smaSeries.setData(smaData);
                emaSeries.setData(emaData);
                bbUpper.setData(bbUp);
                bbMiddle.setData(bbMid);
                bbLower.setData(bbLow);
                rsiSeries.setData(rsiData);
                macdSeries.setData(macdData);
                macdSignal.setData(macdSig);
                macdHist.setData(macdH);
                setupWebSocket();
            } else {
                console.warn("No data returned from history API, retaining previous chart state.");
            }
        } catch (error) {
            if (error.name === 'AbortError') return; 
            console.error("Error fetching history:", error);
            document.getElementById("tvchart-container").classList.add("d-none");
            document.getElementById("numeric-fallback").classList.remove("d-none");
            document.getElementById("numeric-fallback").classList.add("d-flex");
            setupWebSocket();
        } finally {
            loadingSpinner.style.display = "none";
        }
    }
    let wsReconnectTimer = null;
    function setupWebSocket() {
        if (ws) {
            ws.onclose = null;
            ws.close();
        }
        ws = new WebSocket("wss://ws-feed.exchange.coinbase.com");
        ws.onopen = () => {
            console.log("WebSocket connected");
            ws.send(JSON.stringify({
                type: "subscribe",
                product_ids: ["BTC-USD"],
                channels: ["ticker"]
            }));
        };
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "ticker") {
                const price = parseFloat(data.price);
                const timeStr = data.time; 
                let timestamp = Math.floor(new Date(timeStr).getTime() / 1000);
                const intervalMs = getIntervalSeconds(currentInterval);
                timestamp = timestamp - (timestamp % intervalMs);
                
                const localTimestamp = timestamp;
                
                if (lastCandle) {
                    let updatedCandle = { ...lastCandle };
                    if (localTimestamp === lastCandle.time) {
                        updatedCandle.close = price;
                        updatedCandle.high = Math.max(lastCandle.high, price);
                        updatedCandle.low = Math.min(lastCandle.low, price);
                    } else if (localTimestamp > lastCandle.time) {
                        updatedCandle = {
                            time: localTimestamp,
                            open: price,
                            high: price,
                            low: price,
                            close: price
                        };
                    }
                    candleSeries.update(updatedCandle);
                    lastCandle = updatedCandle;
                }
                const fallbackEl = document.getElementById("fallback-live-price");
                if (fallbackEl) {
                    fallbackEl.innerText = "$" + price.toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2});
                    fallbackEl.style.color = "#00d2ff";
                    setTimeout(() => { fallbackEl.style.color = "white"; }, 500);
                }
            }
        };
        ws.onerror = (err) => {
            console.error("WebSocket error:", err);
        };
        ws.onclose = () => {
            console.log("WebSocket disconnected, reconnecting in 3 seconds...");
            clearTimeout(wsReconnectTimer);
            wsReconnectTimer = setTimeout(setupWebSocket, 3000);
        };
    }
    function getIntervalSeconds(interval) {
        const map = { 
            "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
            "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600, "12h": 43200, "1d": 86400 
        };
        return map[interval] || 60;
    }
    let predictionHistory = [];
    let currentCarouselIndex = 0;

    function renderCarousel() {
        if (!predictionHistory.length) return;
        const item = predictionHistory[currentCarouselIndex];
        
        document.getElementById("val-naik").innerText = item.naik.toFixed(1);
        document.getElementById("val-turun").innerText = item.turun.toFixed(1);
        
        const circleNaik = document.getElementById("circle-naik");
        if (circleNaik) circleNaik.style.strokeDashoffset = 264 - (item.naik / 100) * 264;
        
        const volEl = document.getElementById("val-volume");
        if (volEl && item.volume !== undefined) {
            volEl.innerText = item.volume >= 1000000 ? (item.volume / 1000000).toFixed(2) + "M" : (item.volume >= 1000 ? (item.volume / 1000).toFixed(2) + "K" : item.volume.toFixed(2));
        }
        
        const volaEl = document.getElementById("val-volatility");
        if (volaEl && item.volatility !== undefined) {
            volaEl.innerText = item.volatility.toFixed(4);
        }
        
        const rsiEl = document.getElementById("val-rsi");
        if (rsiEl && item.rsi !== undefined) rsiEl.innerText = item.rsi.toFixed(2);
        
        const macdEl = document.getElementById("val-macd");
        if (macdEl && item.macd !== undefined) {
            macdEl.innerText = item.macd.toFixed(2);
            macdEl.className = item.macd > 0 ? "fw-bold text-success font-monospace fs-5" : "fw-bold text-danger font-monospace fs-5";
        }
        
        const adxEl = document.getElementById("val-adx");
        if (adxEl && item.adx !== undefined) adxEl.innerText = item.adx.toFixed(2);
        
        const trendEl = document.getElementById("val-trend");
        if (trendEl && item.trend !== undefined) {
            trendEl.innerText = item.trend;
            trendEl.className = item.trend === "BULLISH" ? "fw-bold text-success font-monospace fs-5" : "fw-bold text-danger font-monospace fs-5";
        }
        
        if (item.target_timestamp) {
            const date = new Date(item.target_timestamp);
            const endDateObj = new Date(date.getTime() + 3600000);
            
            const day = date.getDate();
            const months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"];
            const monthName = months[date.getMonth()];
            const year = date.getFullYear();
            const hours = date.getHours().toString().padStart(2, '0');
            const minutes = date.getMinutes().toString().padStart(2, '0');
            
            const endHours = endDateObj.getHours().toString().padStart(2, '0');
            const endMinutes = endDateObj.getMinutes().toString().padStart(2, '0');
            
            let tzName = "";
            try {
                const tzParts = new Intl.DateTimeFormat('id-ID', { timeZoneName: 'short' }).formatToParts(date);
                const tzPart = tzParts.find(p => p.type === 'timeZoneName');
                if (tzPart) tzName = tzPart.value;
            } catch (e) {
                tzName = "";
            }
            
            document.getElementById("pred-time").innerText = `Waktu Prediksi Untuk ${day} ${monthName} ${year}, ${hours}:${minutes} - ${endHours}:${endMinutes} ${tzName}`.trim();
        } else if (item.target_time) {
            document.getElementById("pred-time").innerText = item.target_time;
        }

        const stampEl = document.getElementById("validation-stamp");
        const stampText = document.getElementById("stamp-text");
        const stampContainer = document.getElementById("stamp-container");
        const pricesContainer = document.getElementById("stamp-prices");
        const startPriceEl = document.getElementById("stamp-start-price");
        const endPriceEl = document.getElementById("stamp-end-price");
        
        if (currentCarouselIndex === 0) {
            document.getElementById("btn-pred-next").disabled = true;
        } else {
            document.getElementById("btn-pred-next").disabled = false;
        }
        
        stampEl.classList.remove("d-none");
        
        if (item.start_price !== undefined && item.end_price !== undefined) {
                pricesContainer.classList.remove("d-none");
                pricesContainer.classList.add("d-flex");
                startPriceEl.innerText = "$" + item.start_price.toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2});
                if (item.end_price === null) {
                    endPriceEl.innerText = "Menunggu...";
                } else {
                    endPriceEl.innerText = "$" + item.end_price.toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2});
                }
            } else {
                pricesContainer.classList.add("d-none");
                pricesContainer.classList.remove("d-flex");
            }

            if (item.status === "VALID") {
                const direction = item.actual_dir || (item.naik > 50 ? "UPTREND" : "DOWNTREND");
                stampText.innerText = `✅ [ VALID ] ${direction} TERKONFIRMASI`;
                stampText.className = "m-0 fw-bolder text-uppercase text-success";
                stampContainer.style.borderLeftColor = "#26a69a";
                stampContainer.style.background = "rgba(13, 17, 23, 0.85)";
            } else if (item.status === "INVALID") {
                const direction = item.actual_dir || (item.naik > 50 ? "DOWNTREND" : "UPTREND");
                stampText.innerText = `❌ [ INVALID ] ${direction} TERJADI`;
                stampText.className = "m-0 fw-bolder text-uppercase text-danger";
                stampContainer.style.borderLeftColor = "#ef5350";
                stampContainer.style.background = "rgba(13, 17, 23, 0.85)";
            } else {
                stampText.innerText = "⏳ [ PENDING ] OBSERVASI BERLANGSUNG";
                stampText.className = "m-0 fw-bolder text-uppercase text-warning";
                stampContainer.style.borderLeftColor = "#FF9800";
                stampContainer.style.background = "rgba(13, 17, 23, 0.85)";
            }
        
        if (currentCarouselIndex >= predictionHistory.length - 1) {
            document.getElementById("btn-pred-prev").disabled = true;
        } else {
            document.getElementById("btn-pred-prev").disabled = false;
        }
    }

    document.getElementById("btn-pred-prev").addEventListener("click", () => {
        if (currentCarouselIndex < predictionHistory.length - 1) {
            currentCarouselIndex++;
            renderCarousel();
        }
    });
    
    document.getElementById("btn-pred-next").addEventListener("click", () => {
        if (currentCarouselIndex > 0) {
            currentCarouselIndex--;
            renderCarousel();
        }
    });

    async function updatePrediction() {
        try {
            const res = await fetch("https://alicelieselou-xgbcoin-api.hf.space/api/predict");
            if (!res.ok) throw new Error("API returned " + res.status);
            const data = await res.json();
            document.getElementById("prediction-boxes").classList.remove("d-none");
            document.getElementById("prediction-failure").classList.add("d-none");
            document.getElementById("prediction-failure").classList.remove("d-block");
            document.getElementById("pred-time").classList.remove("text-danger");
            document.getElementById("btn-pred-prev").classList.remove("d-none");
            document.getElementById("btn-pred-next").classList.remove("d-none");
            
            predictionHistory = data.history ? [data.current, ...data.history] : [data];
            
            // Ensure we don't go out of bounds if history shrinks
            if (currentCarouselIndex >= predictionHistory.length) {
                currentCarouselIndex = Math.max(0, predictionHistory.length - 1);
            }
            
            renderCarousel();
        } catch (e) {
            console.error("Failed to fetch prediction");
            document.getElementById("prediction-boxes").classList.add("d-none");
            document.getElementById("prediction-failure").classList.remove("d-none");
            document.getElementById("prediction-failure").classList.add("d-block");
            document.getElementById("pred-time").innerText = "Prediksi Sementara Tidak Tersedia";
            document.getElementById("pred-time").classList.add("text-danger");
            document.getElementById("btn-pred-prev").classList.add("d-none");
            document.getElementById("btn-pred-next").classList.add("d-none");
        }
    }
    document.querySelectorAll(".timeframe-group button").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".timeframe-group button").forEach(b => b.classList.remove("active"));
            e.target.classList.add("active");
            currentInterval = e.target.getAttribute("data-interval");
            loadHistory(currentInterval);
        });
    });
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") {
            loadHistory(currentInterval);
        }
    });
    loadHistory(currentInterval);
    updatePrediction();
    setInterval(updatePrediction, 5000);
});
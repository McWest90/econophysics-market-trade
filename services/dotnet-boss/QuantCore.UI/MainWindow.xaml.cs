using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Windows;
using Microsoft.EntityFrameworkCore;
using QuantCore.UI.Data;
using ScottPlot;
using Newtonsoft.Json.Linq;

namespace QuantCore.UI
{
    public class ZScorePoint
    {
        public DateTime time { get; set; }
        public double z_score { get; set; }
    }

    public partial class MainWindow : Window
    {
        private readonly HttpClient _httpClient = new HttpClient();

        public MainWindow()
        {
            InitializeComponent();
            SetupCharts();
        }

        private void SetupCharts()
        {
            var darkBg = ScottPlot.Color.FromHex("#1e1e1e");
            var dataBg = ScottPlot.Color.FromHex("#252526");
            var gridColor = ScottPlot.Color.FromHex("#404040");
            var tickColor = ScottPlot.Color.FromHex("#d7d7d7");

            MainChart.Plot.Axes.DateTimeTicksBottom();
            MainChart.Plot.FigureBackground.Color = darkBg;
            MainChart.Plot.DataBackground.Color = dataBg;
            MainChart.Plot.Axes.Color(tickColor);
            MainChart.Plot.Grid.MajorLineColor = gridColor;

            IndicatorChart.Plot.Axes.DateTimeTicksBottom();
            IndicatorChart.Plot.FigureBackground.Color = darkBg;
            IndicatorChart.Plot.DataBackground.Color = dataBg;
            IndicatorChart.Plot.Axes.Color(tickColor);
            IndicatorChart.Plot.Grid.MajorLineColor = gridColor;
            IndicatorChart.Plot.Title("Physics Z-Score (Signal < -2.0)");

            Action SyncX = () => 
            {
                var limits = MainChart.Plot.Axes.GetLimits();
                IndicatorChart.Plot.Axes.SetLimitsX(limits.Left, limits.Right);
                IndicatorChart.Refresh();
            };
            MainChart.MouseWheel += (s, e) => SyncX();
            MainChart.MouseUp += (s, e) => SyncX();
            MainChart.MouseMove += (s, e) =>
            {
                if (e.LeftButton == System.Windows.Input.MouseButtonState.Pressed ||
                    e.RightButton == System.Windows.Input.MouseButtonState.Pressed)
                {
                    SyncX();
                }
            };
        }

        private async void LoadData_Click(object sender, RoutedEventArgs e)
        {
            string ticker = TickerInput.Text.ToUpper();
            
            try
            {
                using var db = new AppDbContext();
                
                var candlesQuery = await db.Candles
                    .Where(c => c.Ticker == ticker)
                    .OrderByDescending(c => c.Time)
                    .Take(500)
                    .ToListAsync();

                var candles = candlesQuery.OrderBy(c => c.Time).ToList();

                if (candles.Count == 0)
                {
                    MessageBox.Show($"Нет данных для {ticker}. Запустите Python-сборщик!");
                    return;
                }

                MainChart.Plot.Clear();
                var ohlcs = new List<OHLC>();
                foreach (var c in candles)
                {
                    ohlcs.Add(new OHLC(
                        c.Open, c.High, c.Low, c.Close, 
                        c.Time, TimeSpan.FromMinutes(1)
                    ));
                }

                var candlePlot = MainChart.Plot.Add.Candlestick(ohlcs);
                
                var green = ScottPlot.Color.FromHex("#32CD32");
                var red = ScottPlot.Color.FromHex("#FF4500");
                
                candlePlot.RisingFillStyle.Color = green;
                candlePlot.RisingLineStyle.Color = green;
                candlePlot.FallingFillStyle.Color = red;
                candlePlot.FallingLineStyle.Color = red;

                MainChart.Plot.Title($"{ticker} Market Data ({candles.Count} bars)");
                MainChart.Plot.Axes.AutoScale();
                MainChart.Refresh();

                IndicatorChart.Plot.Clear();

                try 
                {
                    var url = $"http://localhost:8000/indicators/{ticker}";
                    var response = await _httpClient.GetStringAsync(url);
                    var zScores = Newtonsoft.Json.JsonConvert.DeserializeObject<List<ZScorePoint>>(response);

                    if (zScores != null && zScores.Count > 0)
                    {
                        var xs = zScores.Select(z => z.time.ToOADate()).ToArray();
                        var ys = zScores.Select(z => z.z_score).ToArray();

                        var sigPlot = IndicatorChart.Plot.Add.Scatter(xs, ys);
                        sigPlot.Color = ScottPlot.Color.FromHex("#00BFFF");
                        sigPlot.LineWidth = 2;
                        
                        sigPlot.MarkerSize = 0; 

                        var limitLine = IndicatorChart.Plot.Add.HorizontalLine(-2.0);
                        limitLine.Color = ScottPlot.Color.FromHex("#FF0000");
                        limitLine.LinePattern = ScottPlot.LinePattern.Dashed;
                        
                        var zeroLine = IndicatorChart.Plot.Add.HorizontalLine(0);
                        zeroLine.Color = ScottPlot.Color.FromHex("#555555");

                        IndicatorChart.Plot.Axes.AutoScale();
                        IndicatorChart.Refresh();
                    }
                }
                catch (Exception ex)
                {
                    AiResultText.Text = $"Indicator Error: {ex.Message}";
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Ошибка БД: {ex.Message}");
            }
        }

        private async void Analyze_Click(object sender, RoutedEventArgs e)
        {
            string ticker = TickerInput.Text.ToUpper();
            AiResultText.Text = "Connecting to Brain...";

            try
            {
                var url = $"http://localhost:8000/predict/{ticker}";
                var response = await _httpClient.GetStringAsync(url);
                
                var json = JObject.Parse(response);
                
                double vol = (double?)json["ai_volatility_prediction"] ?? 0.0;
                string rec = (string?)json["recommendation"] ?? "UNKNOWN";

                AiResultText.Text = $"Vol Forecast: {vol:F4}\nRecommendation: {rec}";
            }
            catch (Exception ex)
            {
                AiResultText.Text = $"Error: {ex.Message}";
            }
        }
    }
}
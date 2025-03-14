using System.Drawing;
using System.Text.RegularExpressions;
using Tesseract;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using EVEMonitor.ImageProcessing.Services;
using EVEMonitor.OCR.Helpers;
using EVEMonitor.OCR.Models;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace EVEMonitor.OCR.Services
{
    /// <summary>
    /// OCR服务实现
    /// </summary>
    public class OcrService : IOcrService, IDisposable
    {
        private readonly ILogger<OcrService> _logger;
        private readonly IConfigService _configService;
        private readonly IImageProcessingService _imageProcessingService;
        private readonly TesseractEngine _engine;
        private readonly Dictionary<string, bool> _dangerousShipTypes = new Dictionary<string, bool>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, bool> _dangerousCorporations = new Dictionary<string, bool>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, bool> _friendlyCorporations = new Dictionary<string, bool>(StringComparer.OrdinalIgnoreCase);
        private bool _disposed = false;

        /// <summary>
        /// 初始化OCR服务
        /// </summary>
        /// <param name="logger">日志记录器</param>
        /// <param name="configService">配置服务</param>
        public OcrService(ILogger<OcrService> logger, IConfigService configService)
        {
            _logger = logger;
            _configService = configService;
            _imageProcessingService = new ImageProcessingService(
                new Logger<ImageProcessingService>(new NullLoggerFactory()),
                configService);

            var tessDataPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "tessdata");
            if (!Directory.Exists(tessDataPath))
            {
                Directory.CreateDirectory(tessDataPath);
            }

            _engine = new TesseractEngine(tessDataPath, "eng", EngineMode.Default);
            _engine.SetVariable("tessedit_char_whitelist", "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-[]");

            // 从配置中加载危险实体
            var config = configService.CurrentConfig;
            if (config.DangerousShipTypes != null)
            {
                foreach (var shipType in config.DangerousShipTypes)
                {
                    _dangerousShipTypes[shipType] = true;
                }
            }

            if (config.DangerousCorporations != null)
            {
                foreach (var corp in config.DangerousCorporations)
                {
                    _dangerousCorporations[corp] = true;
                }
            }

            if (config.FriendlyCorporations != null)
            {
                foreach (var corp in config.FriendlyCorporations)
                {
                    _friendlyCorporations[corp] = true;
                }
            }
        }

        /// <summary>
        /// 识别星系名称
        /// </summary>
        /// <param name="image">星系名称区域图像</param>
        /// <returns>识别的星系名称</returns>
        public string RecognizeSystemName(Bitmap image)
        {
            if (image == null)
                return string.Empty;

            try
            {
                var processedImage = _imageProcessingService.PreprocessImage(image);
                using var pix = ConvertBitmapToPix(processedImage);
                using var page = _engine.Process(pix);
                var text = page.GetText().Trim();

                return text;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "识别系统名称时发生错误");
                return string.Empty;
            }
        }

        /// <summary>
        /// 识别舰船表格
        /// </summary>
        /// <param name="image">舰船表格区域图像</param>
        /// <returns>识别的舰船信息列表</returns>
        public List<ShipInfo> RecognizeShipTable(Bitmap image)
        {
            if (image == null)
                return new List<ShipInfo>();

            try
            {
                var processedImage = _imageProcessingService.PreprocessImage(image);
                using var pix = ConvertBitmapToPix(processedImage);
                using var page = _engine.Process(pix);
                var text = page.GetText().Trim();
                var lines = text.Split('\n', StringSplitOptions.RemoveEmptyEntries);
                var ships = new List<ShipInfo>();

                foreach (var line in lines)
                {
                    var ship = ParseShipLine(line);
                    if (ship != null)
                    {
                        ship.LastUpdated = DateTime.Now;
                        ship.IsDangerous = IsDangerousShip(ship);
                        ship.Status = DetermineShipStatus(ship);
                        ship.ThreatLevel = CalculateThreatLevel(ship);
                        ships.Add(ship);
                    }
                }

                return ships;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "识别舰船表格时发生错误");
                return new List<ShipInfo>();
            }
        }

        /// <summary>
        /// 处理识别结果
        /// </summary>
        /// <param name="emulatorIndex">模拟器索引</param>
        /// <param name="systemName">星系名称</param>
        /// <param name="ships">舰船信息列表</param>
        /// <returns>模拟器识别结果</returns>
        public EmulatorRecognitionResult ProcessRecognitionResult(int emulatorIndex, string systemName, List<ShipInfo> ships)
        {
            return new EmulatorRecognitionResult
            {
                EmulatorIndex = emulatorIndex,
                SystemName = systemName,
                Ships = ships,
                ContainsDangerousShips = ships.Any(s => s.IsDangerous),
                Timestamp = DateTime.Now
            };
        }

        private bool IsDangerousShip(ShipInfo ship)
        {
            return _dangerousShipTypes.ContainsKey(ship.Type) ||
                   _dangerousCorporations.ContainsKey(ship.Corporation);
        }

        private ShipStatus DetermineShipStatus(ShipInfo ship)
        {
            if (_friendlyCorporations.ContainsKey(ship.Corporation))
                return ShipStatus.Friendly;
            if (_dangerousCorporations.ContainsKey(ship.Corporation))
                return ShipStatus.Hostile;
            if (_dangerousShipTypes.ContainsKey(ship.Type))
                return ShipStatus.Neutral;
            return ShipStatus.Normal;
        }

        private int CalculateThreatLevel(ShipInfo ship)
        {
            if (ship.Status == ShipStatus.Hostile)
                return 5;
            if (ship.Status == ShipStatus.Neutral)
                return 3;
            if (ship.Status == ShipStatus.Friendly)
                return 0;
            return 1;
        }

        private ShipInfo? ParseShipLine(string line)
        {
            try
            {
                // 匹配格式：舰船名称 [军团] - 舰船类型 - 距离
                var corporationMatch = Regex.Match(line, @"\[(.*?)\]");
                string corporation = corporationMatch.Success ? corporationMatch.Groups[1].Value : string.Empty;

                // 移除军团部分以便处理其他字段
                string textWithoutCorp = corporationMatch.Success
                    ? line.Replace(corporationMatch.Value, "").Trim()
                    : line;

                // 分割剩余部分
                string[] parts = textWithoutCorp.Split(new[] { '-' }, StringSplitOptions.RemoveEmptyEntries);

                var ship = new ShipInfo
                {
                    Name = parts.Length > 0 ? parts[0].Trim() : string.Empty,
                    Corporation = corporation,
                    Type = parts.Length > 1 ? parts[1].Trim() : string.Empty
                };

                // 解析距离
                if (parts.Length > 2)
                {
                    string distancePart = parts[2].Trim();
                    var distanceMatch = Regex.Match(distancePart, @"(\d+(\.\d+)?)\s*km");
                    if (distanceMatch.Success)
                    {
                        double.TryParse(distanceMatch.Groups[1].Value, out double distance);
                        ship.Distance = distance;
                    }
                }

                return ship;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "解析舰船信息行时发生错误: {Line}", line);
                return null;
            }
        }

        private Pix ConvertBitmapToPix(Bitmap bitmap)
        {
            using var ms = new MemoryStream();
            bitmap.Save(ms, System.Drawing.Imaging.ImageFormat.Png);
            ms.Position = 0;
            return Pix.LoadFromMemory(ms.ToArray());
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                _engine?.Dispose();
                _disposed = true;
            }
        }
    }
}
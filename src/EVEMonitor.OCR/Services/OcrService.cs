using System.Drawing;
using System.Text.RegularExpressions;
using Tesseract;
using EVEMonitor.Core.Interfaces;
using EVEMonitor.Core.Models;
using EVEMonitor.ImageProcessing.Services;

namespace EVEMonitor.OCR.Services
{
    /// <summary>
    /// OCR服务实现
    /// </summary>
    public class OcrService : IOcrService, IDisposable
    {
        private readonly TesseractEngine _engine;
        private readonly ImageProcessingService _imageProcessingService;
        private readonly string _dataPath;
        private readonly string _language;
        private readonly List<string> _knownSystems = new List<string>();
        private readonly Dictionary<string, bool> _dangerousShipTypes = new Dictionary<string, bool>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, bool> _dangerousCorporations = new Dictionary<string, bool>(StringComparer.OrdinalIgnoreCase);
        private readonly Dictionary<string, bool> _friendlyCorporations = new Dictionary<string, bool>(StringComparer.OrdinalIgnoreCase);
        private bool _disposed = false;

        /// <summary>
        /// 初始化OCR服务
        /// </summary>
        /// <param name="dataPath">Tesseract数据路径</param>
        /// <param name="language">OCR语言</param>
        /// <param name="imageProcessingService">图像处理服务</param>
        public OcrService(string dataPath = "./tessdata", string language = "eng+chi_sim", ImageProcessingService imageProcessingService = null)
        {
            _dataPath = dataPath;
            _language = language;
            _imageProcessingService = imageProcessingService ?? new ImageProcessingService();

            // 确保数据目录存在
            if (!Directory.Exists(_dataPath))
            {
                Directory.CreateDirectory(_dataPath);
            }

            _engine = new TesseractEngine(_dataPath, _language, EngineMode.Default);
            
            // 加载已知星系名称列表
            LoadKnownSystems();
            
            // 加载危险舰船类型和军团列表
            LoadDangerousEntities();
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
                // 预处理图像以提高OCR识别率
                using (var processedImage = _imageProcessingService?.PreprocessImage(image) ?? image)
                {
                    using (var page = _engine.Process(processedImage))
                    {
                        string text = page.GetText().Trim();
                        
                        // 清理文本，移除多余空格和换行
                        text = Regex.Replace(text, @"\s+", " ").Trim();
                        
                        // 尝试匹配已知星系名称
                        string matchedSystem = FindBestMatchingSystem(text);
                        if (!string.IsNullOrEmpty(matchedSystem))
                        {
                            return matchedSystem;
                        }
                        
                        return text;
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"识别星系名称失败: {ex.Message}");
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

            var ships = new List<ShipInfo>();

            try
            {
                // 预处理图像
                using (var processedImage = _imageProcessingService?.PreprocessImage(image) ?? image)
                {
                    using (var page = _engine.Process(processedImage))
                    {
                        string text = page.GetText();
                        
                        // 按行分割文本
                        string[] lines = text.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                        foreach (var line in lines)
                        {
                            string trimmedLine = line.Trim();
                            if (string.IsNullOrEmpty(trimmedLine))
                                continue;
                                
                            // 解析舰船信息
                            var ship = ParseShipInfo(trimmedLine);
                            if (ship != null)
                            {
                                ships.Add(ship);
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"识别舰船表格失败: {ex.Message}");
            }

            // 检查舰船信息并标记危险
            foreach (var ship in ships)
            {
                CheckShipDangerStatus(ship);
            }

            return ships;
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
                Timestamp = DateTime.Now
            };
        }

        /// <summary>
        /// 解析舰船信息
        /// </summary>
        /// <param name="text">舰船文本行</param>
        /// <returns>解析的舰船信息</returns>
        private ShipInfo ParseShipInfo(string text)
        {
            // 这里实现简单的解析逻辑，实际应用中可能需要更复杂的正则表达式匹配
            // 格式可能是: 舰船名称 [军团] - 舰船类型 - 距离
            
            // 匹配军团名称 [xxx]
            var corporationMatch = Regex.Match(text, @"\[(.*?)\]");
            string corporation = corporationMatch.Success ? corporationMatch.Groups[1].Value : string.Empty;
            
            // 移除军团部分以便处理其他字段
            string textWithoutCorp = corporationMatch.Success 
                ? text.Replace(corporationMatch.Value, "").Trim() 
                : text;
            
            // 尝试分割剩余部分
            string[] parts = textWithoutCorp.Split(new[] { '-' }, StringSplitOptions.RemoveEmptyEntries);
            
            // 创建舰船信息对象
            var ship = new ShipInfo
            {
                Name = parts.Length > 0 ? parts[0].Trim() : text.Trim(),
                Corporation = corporation,
                Type = parts.Length > 1 ? parts[1].Trim() : string.Empty
            };
            
            // 尝试解析距离
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

        /// <summary>
        /// 检查舰船危险状态
        /// </summary>
        /// <param name="ship">舰船信息</param>
        private void CheckShipDangerStatus(ShipInfo ship)
        {
            // 检查是否是危险舰船类型
            bool isDangerousType = !string.IsNullOrEmpty(ship.Type) && 
                                  _dangerousShipTypes.ContainsKey(ship.Type);
            
            // 检查是否是危险军团
            bool isDangerousCorp = !string.IsNullOrEmpty(ship.Corporation) && 
                                  _dangerousCorporations.ContainsKey(ship.Corporation);
            
            // 检查是否是友好军团
            bool isFriendlyCorp = !string.IsNullOrEmpty(ship.Corporation) && 
                                 _friendlyCorporations.ContainsKey(ship.Corporation);
            
            // 设置危险状态
            ship.IsDangerous = isDangerousType || isDangerousCorp;
            
            // 设置舰船状态
            if (isFriendlyCorp)
            {
                ship.Status = ShipStatus.Friendly;
                ship.IsDangerous = false; // 友好军团舰船不危险
            }
            else if (isDangerousCorp)
            {
                ship.Status = ShipStatus.Hostile;
                ship.ThreatLevel = 5; // 最高威胁等级
            }
            else if (isDangerousType)
            {
                ship.Status = ShipStatus.Neutral;
                ship.ThreatLevel = 3; // 中等威胁等级
            }
            else
            {
                ship.Status = ShipStatus.Normal;
                ship.ThreatLevel = 1; // 低威胁等级
            }
        }

        /// <summary>
        /// 查找最佳匹配星系名称
        /// </summary>
        /// <param name="text">识别的文本</param>
        /// <returns>匹配的星系名称</returns>
        private string FindBestMatchingSystem(string text)
        {
            // 简单实现，直接查找完全匹配
            // 实际应用中可能需要使用模糊匹配算法如Levenshtein距离
            foreach (var system in _knownSystems)
            {
                if (string.Equals(text, system, StringComparison.OrdinalIgnoreCase))
                {
                    return system;
                }
            }
            
            return string.Empty;
        }

        /// <summary>
        /// 加载已知星系名称
        /// </summary>
        private void LoadKnownSystems()
        {
            try
            {
                // 实际应用中这里可以从配置文件或数据库加载
                // 这里只添加一些示例星系名称作为演示
                _knownSystems.AddRange(new[]
                {
                    "Jita", "Amarr", "Dodixie", "Rens", "Hek",
                    "Perimeter", "Niarja", "New Caldari", "Oursulaert", "Isanamo",
                    // 添加中文星系名称
                    "吉他", "埃玛", "多迪西", "伦斯", "赫克"
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"加载星系名称失败: {ex.Message}");
            }
        }

        /// <summary>
        /// 加载危险实体列表
        /// </summary>
        private void LoadDangerousEntities()
        {
            try
            {
                // 危险舰船类型
                string[] dangerousTypes = new[]
                {
                    "Battleship", "Carrier", "Dreadnought", "Titan", "Supercarrier",
                    "战列舰", "航母", "无畏舰", "泰坦", "超级航母"
                };
                
                foreach (var type in dangerousTypes)
                {
                    _dangerousShipTypes[type] = true;
                }
                
                // 危险军团
                string[] dangerousCorporations = new[]
                {
                    "CODE.", "Goonswarm", "Pandemic Legion",
                    "代码联盟", "蜂群", "流行军团"
                };
                
                foreach (var corp in dangerousCorporations)
                {
                    _dangerousCorporations[corp] = true;
                }
                
                // 友好军团
                string[] friendlyCorporations = new[]
                {
                    "Our Corp", "Friendly Alliance",
                    "我方公司", "友好联盟"
                };
                
                foreach (var corp in friendlyCorporations)
                {
                    _friendlyCorporations[corp] = true;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"加载危险实体列表失败: {ex.Message}");
            }
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        /// <summary>
        /// 释放资源
        /// </summary>
        /// <param name="disposing">是否释放托管资源</param>
        protected virtual void Dispose(bool disposing)
        {
            if (_disposed)
                return;

            if (disposing)
            {
                _engine?.Dispose();
            }

            _disposed = true;
        }
    }
} 
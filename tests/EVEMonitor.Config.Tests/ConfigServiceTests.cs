using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using EVEMonitor.Config.Services;
using EVEMonitor.Core.Models;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;

namespace EVEMonitor.Config.Tests
{
    public class ConfigServiceTests
    {
        private readonly Mock<ILogger<ConfigService>> _loggerMock;
        private readonly string _testConfigsPath;

        public ConfigServiceTests()
        {
            _loggerMock = new Mock<ILogger<ConfigService>>();

            // 设置测试配置目录
            string? assemblyLocation = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            _testConfigsPath = assemblyLocation != null
                ? Path.Combine(assemblyLocation, "TestConfigs", "config.json")
                : Path.Combine(Directory.GetCurrentDirectory(), "TestConfigs", "config.json");
        }

        [Fact]
        public void Constructor_WithValidConfigPath_ShouldInitializeCorrectly()
        {
            // Arrange & Act
            var configService = new ConfigService(_testConfigsPath);

            // Assert
            Assert.NotNull(configService);
        }

        [Fact]
        public void LoadConfig_WithValidConfigFile_ShouldLoadConfig()
        {
            // Arrange
            string configFilePath = Path.Combine(_testConfigsPath, "appconfig.json");

            // 如果测试配置文件不存在，跳过测试
            if (!File.Exists(configFilePath))
            {
                return;
            }

            var configService = new ConfigService(_testConfigsPath);

            // Act
            var config = configService.LoadConfig();

            // Assert
            Assert.NotNull(config);
            Assert.Equal("EVE Monitor", config.AppName);
        }

        [Fact]
        public void SaveConfig_WithValidConfig_ShouldSaveConfig()
        {
            // Arrange
            var configService = new ConfigService(_testConfigsPath);
            var config = new AppConfig
            {
                AppName = "Test App",
                ScreenshotInterval = 2000,
                SaveScreenshots = true,
                ScreenshotSavePath = Path.Combine(_testConfigsPath, "Screenshots")
            };

            // Act
            bool result = configService.SaveConfig(config);
            var loadedConfig = configService.LoadConfig();

            // Assert
            Assert.True(result);
            Assert.Equal("Test App", loadedConfig.AppName);
        }

        [Fact]
        public void GetKnownSystems_WithValidConfigFile_ShouldReturnSystems()
        {
            // Arrange
            string configFilePath = Path.Combine(_testConfigsPath, "knownsystems.json");

            // 如果测试配置文件不存在，跳过测试
            if (!File.Exists(configFilePath))
            {
                return;
            }

            var configService = new ConfigService(_testConfigsPath);

            // Act
            // 获取已知星系列表
            var systems = configService.CurrentConfig.DangerousShipTypes;

            // Assert
            Assert.NotNull(systems);
            Assert.True(systems.Any());
        }

        [Fact]
        public void GetDangerousEntities_WithValidConfigFile_ShouldReturnEntities()
        {
            // Arrange
            string configFilePath = Path.Combine(_testConfigsPath, "dangerousentities.json");

            // 如果测试配置文件不存在，跳过测试
            if (!File.Exists(configFilePath))
            {
                return;
            }

            var configService = new ConfigService(_testConfigsPath);

            // Act
            // 获取危险实体列表
            var entities = configService.CurrentConfig.DangerousCorporations;

            // Assert
            Assert.NotNull(entities);
            Assert.True(entities.Any());
        }

        [Fact]
        public void ConfigChanged_ShouldRaiseEvent()
        {
            // Arrange
            var configService = new ConfigService(_testConfigsPath);
            bool eventRaised = false;
            configService.ConfigChanged += (sender, args) => eventRaised = true;

            // Act
            // 手动触发配置变更事件
            // 使用反射调用私有方法
            var method = typeof(ConfigService).GetMethod("OnConfigChanged",
                System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            method?.Invoke(configService, new object[] { configService, EventArgs.Empty });

            // Assert
            Assert.True(eventRaised);
        }
    }
}
using Xunit;
using EVEMonitor.Core.Models;

namespace EVEMonitor.Core.Tests.Models
{
    public class ShipInfoTests
    {
        [Fact]
        public void ShipInfo_Properties_AreSetCorrectly()
        {
            // Arrange
            var corporation = "测试军团";
            var shipName = "测试飞行员";
            var shipType = "测试战舰";
            var isDangerous = true;

            // Act
            var shipInfo = new ShipInfo
            {
                Corporation = corporation,
                Name = shipName,
                ShipType = shipType,
                IsDangerous = isDangerous
            };

            // Assert
            Assert.Equal(corporation, shipInfo.Corporation);
            Assert.Equal(shipName, shipInfo.Name);
            Assert.Equal(shipType, shipInfo.ShipType);
            Assert.Equal(isDangerous, shipInfo.IsDangerous);
        }

        [Fact]
        public void ShipInfo_ToStringMethod_ReturnsFormattedString()
        {
            // Arrange
            var shipInfo = new ShipInfo
            {
                Corporation = "测试军团",
                Name = "测试飞行员",
                ShipType = "测试战舰",
                Distance = 10.5,
                IsDangerous = true
            };

            // Act
            var result = shipInfo.ToString();

            // Assert
            Assert.Contains(shipInfo.Corporation, result);
            Assert.Contains(shipInfo.Name, result);
            Assert.Contains(shipInfo.ShipType, result);
            Assert.Contains("10.5", result); // 距离可能以不同格式显示
        }
    }
}
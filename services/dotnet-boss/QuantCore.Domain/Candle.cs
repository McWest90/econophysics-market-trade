using System;
using System.ComponentModel.DataAnnotations.Schema;

namespace QuantCore.Domain
{
    [Table("candles")]
    public class Candle
    {
        
        [Column("ticker")]
        public string Ticker { get; set; } = string.Empty;

        [Column("time")]
        public DateTime Time { get; set; }

        [Column("open")]
        public double Open { get; set; }

        [Column("high")]
        public double High { get; set; }

        [Column("low")]
        public double Low { get; set; }

        [Column("close")]
        public double Close { get; set; }

        [Column("volume")]
        public long Volume { get; set; }

        [Column("volatility")]
        public double Volatility { get; set; }
    }
}
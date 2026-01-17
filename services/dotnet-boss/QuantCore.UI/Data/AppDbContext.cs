using Microsoft.EntityFrameworkCore;
using QuantCore.Domain;

namespace QuantCore.UI.Data
{
    public class AppDbContext : DbContext
    {
        public DbSet<Candle> Candles { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            optionsBuilder.UseNpgsql("Host=localhost;Port=5432;Database=quant_db;Username=quant_user;Password=quant_pass");
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<Candle>()
                .HasKey(c => new { c.Ticker, c.Time });
        }
    }
}
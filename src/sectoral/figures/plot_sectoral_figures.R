# Sectoral extension figures (empirical PNAD parameters)
# Reads SECTOR_AREQ_EMPIRICAL.csv and SECTORAL_PNAD_EMPIRICAL.csv
# Produces figures for the paper's sectoral extension section

library(ggplot2)
library(dplyr)

# -- Paths --
base_dir <- Sys.getenv("JORNADA_BASE_DIR", unset = getwd())
results_path <- file.path(base_dir, "output/sectoral/tables/SECTOR_AREQ_EMPIRICAL.csv")
facts_path <- file.path(base_dir, "data_final/SECTORAL_PNAD_EMPIRICAL.csv")
fig_dir <- file.path(base_dir, "output/sectoral/figures")
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

# -- Load data --
results <- read.csv(results_path, stringsAsFactors = FALSE)
facts <- read.csv(facts_path, stringsAsFactors = FALSE)

sector_labels <- c(
  "agriculture" = "Agriculture",
  "industry" = "Industry",
  "services" = "Services",
  "AGGREGATE" = "Aggregate"
)

results <- results %>%
  mutate(sector_label = factor(
    ifelse(sector %in% names(sector_labels), sector_labels[sector], sector),
    levels = c("Agriculture", "Industry", "Services", "Aggregate")
  ))


# ===================================================================
# FIGURE 1: A_req by sector — side-by-side bar chart (40h and 36h)
# ===================================================================

df1 <- results %>%
  filter(sector != "AGGREGATE") %>%
  mutate(scenario = factor(
    paste0("44 -> ", h1, "h"),
    levels = c("44 -> 40h", "44 -> 36h")
  ))

p1 <- ggplot(df1, aes(x = sector_label, y = A_req_pct, fill = scenario)) +
  geom_col(position = position_dodge(0.7), width = 0.6) +
  geom_text(aes(label = sprintf("%.1f%%", A_req_pct)),
            position = position_dodge(0.7), vjust = -0.5, size = 3.2) +
  scale_fill_manual(values = c("44 -> 40h" = "steelblue", "44 -> 36h" = "firebrick")) +
  labs(
    x = NULL,
    y = expression(A[req] ~ "(%)"),
    fill = NULL
  ) +
  theme_classic(base_size = 12) +
  theme(legend.position = "top") +
  coord_cartesian(ylim = c(0, max(df1$A_req_pct) * 1.2))

ggsave(file.path(fig_dir, "fig1_areq_by_sector.pdf"), p1, width = 6.5, height = 4.5)
ggsave(file.path(fig_dir, "fig1_areq_by_sector.png"), p1, width = 6.5, height = 4.5, dpi = 300)
cat("Saved: fig1_areq_by_sector\n")


# ===================================================================
# FIGURE 3: Scatter — A_req vs informality rate (bubble = emp share)
# ===================================================================

df3 <- results %>%
  filter(sector != "AGGREGATE", h1 == 36)

# National aggregate point (from national model)
national_point <- data.frame(
  inf_target = 0.378,
  A_req_pct = 7.26,
  sector_label = factor("National", levels = levels(df3$sector_label)),
  lambda_s = 1.0
)

p3 <- ggplot(df3, aes(x = inf_target * 100, y = A_req_pct)) +
  geom_point(aes(size = lambda_s * 100, color = sector_label), shape = 16) +
  geom_point(data = national_point,
             aes(x = inf_target * 100, y = A_req_pct),
             shape = 4, size = 4, stroke = 1.2, color = "black") +
  geom_text(aes(label = sector_label), hjust = -0.15, vjust = -0.5, size = 3.5) +
  annotate("text", x = national_point$inf_target * 100 + 2,
           y = national_point$A_req_pct,
           label = "National\n(7.3%)", size = 3, hjust = 0) +
  scale_size_continuous(range = c(3, 12), name = "Employment share (%)") +
  scale_color_manual(values = c(
    "Agriculture" = "#2ca02c",
    "Industry" = "#1f77b4",
    "Services" = "#ff7f0e"
  ), guide = "none") +
  labs(
    x = "Informality Rate (%)",
    y = expression(A[req] ~ "(%)")
  ) +
  theme_classic(base_size = 12) +
  theme(legend.position = c(0.22, 0.85))

ggsave(file.path(fig_dir, "fig3_scatter_areq_informality.pdf"), p3, width = 6.5, height = 4.5)
ggsave(file.path(fig_dir, "fig3_scatter_areq_informality.png"), p3, width = 6.5, height = 4.5, dpi = 300)
cat("Saved: fig3_scatter_areq_informality\n")

cat("\nDone. Figures saved to:", fig_dir, "\n")

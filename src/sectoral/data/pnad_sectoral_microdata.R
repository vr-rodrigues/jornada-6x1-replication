# ============================================================================
# PNAD Continua Microdata: Sectoral Parameters
# ============================================================================
# Downloads PNAD Continua quarterly microdata and computes, BY SECTOR:
#   1. theta_s: hours distribution of formal workers (<=36h, 37-40h, >=41h)
#   2. inf_s: informality rate (IBGE official definition)
#   3. lambda_s: employment share
#   4. avg_hours_s: average weekly hours (total and formal only)
#
# CNAE classification: A = Agriculture, B-F = Industry, G-U = Services
#
# IBGE informality definition:
#   Informal = emp privado sem carteira + domestico sem carteira
#            + empregador sem CNPJ + conta-propria sem CNPJ
#            + trabalhador familiar auxiliar
#   Uses VD4009 (carteira for employees) + V4017 (CNPJ for CP/empregador)
# ============================================================================

library(PNADcIBGE)
library(survey)
library(dplyr)

cat("=", rep("=", 68), "\n", sep = "")
cat("PNAD CONTINUA MICRODATA: SECTORAL PARAMETERS\n")
cat("=", rep("=", 68), "\n", sep = "")

# -- 1. Download microdata ---------------------------------------------------
cat("\n[1] Downloading PNAD Continua microdata...\n")

pnad <- tryCatch({
  cat("  Trying Q4 2024...\n")
  get_pnadc(year = 2024, quarter = 4)
}, error = function(e) {
  cat("  Q4 2024 not available, trying Q3 2024...\n")
  tryCatch({
    get_pnadc(year = 2024, quarter = 3)
  }, error = function(e2) {
    cat("  Q3 2024 not available, trying Q4 2023...\n")
    get_pnadc(year = 2023, quarter = 4)
  })
})

cat("  Download complete.\n")

# -- 2. Extract and classify -------------------------------------------------
cat("\n[2] Classifying workers by sector...\n")

df <- pnad$variables

cat("  V4013 (CNAE): ", class(df$V4013), ", N non-NA: ",
    sum(!is.na(df$V4013)), "\n")
cat("  V4039 (hours): ", class(df$V4039), ", N non-NA: ",
    sum(!is.na(df$V4039)), "\n")
cat("  V4017 (CNPJ): ", class(df$V4017), ", N non-NA: ",
    sum(!is.na(df$V4017)), "\n")

# Filter to occupied persons (V4013 only filled for occupied)
df_occ <- df %>%
  filter(!is.na(V4013))

cat("  Occupied persons with CNAE: ", nrow(df_occ), "\n")

# Classify CNAE into 3 sectors
# V4013 is character. First 2 digits:
#   01-03 (section A) = Agriculture
#   05-43 (sections B-F) = Industry
#   45-99 (sections G-U) = Services
df_occ <- df_occ %>%
  mutate(
    cnae2d = as.integer(substr(V4013, 1, 2)),
    sector = case_when(
      cnae2d >= 1 & cnae2d <= 3   ~ "agriculture",
      cnae2d >= 5 & cnae2d <= 43  ~ "industry",
      cnae2d >= 45 & cnae2d <= 99 ~ "services",
      TRUE ~ NA_character_
    )
  )

cat("  Sector classification:\n")
print(table(df_occ$sector, useNA = "ifany"))

# -- 3. Define informality (IBGE official definition) -------------------------
cat("\n[3] Computing informality by sector...\n")

# VD4009: Posicao na ocupacao (has carteira detail for employees)
# V4017: "Nesse trabalho, tinha CNPJ?" (for Conta-propria and Empregador)
cat("  VD4009 values:\n")
print(table(df_occ$VD4009, useNA = "ifany"))
cat("\n  V4017 values (for CP and Empregador):\n")
print(table(df_occ$V4017, useNA = "ifany"))

# IBGE informality:
# INFORMAL:
#   - Emp privado SEM carteira
#   - Domestico SEM carteira
#   - Empregador SEM CNPJ (V4017 = "Nao")
#   - Conta-propria SEM CNPJ (V4017 = "Nao")
#   - Trabalhador familiar auxiliar
# FORMAL (not informal):
#   - Emp privado COM carteira
#   - Domestico COM carteira
#   - Emp publico COM/SEM carteira (both not counted as informal by IBGE)
#   - Militar e servidor estatutario
#   - Empregador COM CNPJ (V4017 = "Sim")
#   - Conta-propria COM CNPJ (V4017 = "Sim")

vd4009_text <- as.character(df_occ$VD4009)
v4017_text  <- as.character(df_occ$V4017)

df_occ <- df_occ %>%
  mutate(
    vd4009_text = as.character(VD4009),
    v4017_text  = as.character(V4017),
    informal = case_when(
      # Emp privado sem carteira -> INFORMAL
      grepl("privado sem carteira", vd4009_text, ignore.case = TRUE) ~ 1L,
      # Domestico sem carteira -> INFORMAL
      grepl("stico sem carteira", vd4009_text, ignore.case = TRUE) ~ 1L,
      # Trabalhador familiar auxiliar -> INFORMAL
      grepl("familiar auxiliar", vd4009_text, ignore.case = TRUE) ~ 1L,
      # Empregador -> check CNPJ via V4017
      grepl("Empregador", vd4009_text, ignore.case = TRUE) &
        grepl("Sim", v4017_text, ignore.case = TRUE) ~ 0L,  # com CNPJ
      grepl("Empregador", vd4009_text, ignore.case = TRUE) &
        !grepl("Sim", v4017_text, ignore.case = TRUE) ~ 1L, # sem CNPJ
      # Conta-propria -> check CNPJ via V4017
      grepl("Conta", vd4009_text, ignore.case = TRUE) &
        grepl("Sim", v4017_text, ignore.case = TRUE) ~ 0L,  # com CNPJ
      grepl("Conta", vd4009_text, ignore.case = TRUE) &
        !grepl("Sim", v4017_text, ignore.case = TRUE) ~ 1L, # sem CNPJ
      # Emp privado com carteira -> FORMAL
      grepl("privado com carteira", vd4009_text, ignore.case = TRUE) ~ 0L,
      # Domestico com carteira -> FORMAL
      grepl("stico com carteira", vd4009_text, ignore.case = TRUE) ~ 0L,
      # Emp publico (com or sem carteira) -> FORMAL (IBGE def)
      grepl("blico", vd4009_text, ignore.case = TRUE) ~ 0L,
      # Militar e servidor estatutario -> FORMAL
      grepl("Militar", vd4009_text, ignore.case = TRUE) ~ 0L,
      grepl("estatut", vd4009_text, ignore.case = TRUE) ~ 0L,
      TRUE ~ NA_integer_
    ),
    is_formal = ifelse(informal == 0L, 1L, 0L)
  )

cat("\n  Informality classification (VD4009 + V4017 IBGE def):\n")
cat("    Formal: ", sum(df_occ$informal == 0, na.rm = TRUE), "\n")
cat("    Informal: ", sum(df_occ$informal == 1, na.rm = TRUE), "\n")
cat("    NA: ", sum(is.na(df_occ$informal)), "\n")
cat("    National inf rate (unweighted): ",
    round(mean(df_occ$informal, na.rm = TRUE) * 100, 1), "%\n")

# Cross-tab for validation
cat("\n  Validation - Conta-propria by CNPJ:\n")
cp <- df_occ[grepl("Conta", as.character(df_occ$VD4009)), ]
cat("    Com CNPJ (formal): ", sum(cp$informal == 0, na.rm = TRUE), "\n")
cat("    Sem CNPJ (informal): ", sum(cp$informal == 1, na.rm = TRUE), "\n")
cat("  Empregador by CNPJ:\n")
emp <- df_occ[grepl("Empregador", as.character(df_occ$VD4009)), ]
cat("    Com CNPJ (formal): ", sum(emp$informal == 0, na.rm = TRUE), "\n")
cat("    Sem CNPJ (informal): ", sum(emp$informal == 1, na.rm = TRUE), "\n")

# -- 4. Reconstruct survey design with sector variables -----------------------
cat("\n[4] Computing weighted statistics...\n")

# Add new variables to the original survey design object
# Must use VD4009 + V4017 for informality (matching section 3 exactly)
pnad_upd <- update(pnad,
  cnae2d = as.integer(substr(V4013, 1, 2)),
  sector = case_when(
    as.integer(substr(V4013, 1, 2)) >= 1 &
      as.integer(substr(V4013, 1, 2)) <= 3   ~ "agriculture",
    as.integer(substr(V4013, 1, 2)) >= 5 &
      as.integer(substr(V4013, 1, 2)) <= 43  ~ "industry",
    as.integer(substr(V4013, 1, 2)) >= 45 &
      as.integer(substr(V4013, 1, 2)) <= 99 ~ "services",
    TRUE ~ NA_character_
  ),
  informal = {
    vd9 <- as.character(VD4009)
    v17 <- as.character(V4017)
    case_when(
      grepl("privado sem carteira", vd9, ignore.case = TRUE) ~ 1L,
      grepl("stico sem carteira", vd9, ignore.case = TRUE) ~ 1L,
      grepl("familiar auxiliar", vd9, ignore.case = TRUE) ~ 1L,
      grepl("Empregador", vd9, ignore.case = TRUE) &
        grepl("Sim", v17, ignore.case = TRUE) ~ 0L,
      grepl("Empregador", vd9, ignore.case = TRUE) &
        !grepl("Sim", v17, ignore.case = TRUE) ~ 1L,
      grepl("Conta", vd9, ignore.case = TRUE) &
        grepl("Sim", v17, ignore.case = TRUE) ~ 0L,
      grepl("Conta", vd9, ignore.case = TRUE) &
        !grepl("Sim", v17, ignore.case = TRUE) ~ 1L,
      grepl("privado com carteira", vd9, ignore.case = TRUE) ~ 0L,
      grepl("stico com carteira", vd9, ignore.case = TRUE) ~ 0L,
      grepl("blico", vd9, ignore.case = TRUE) ~ 0L,
      grepl("Militar", vd9, ignore.case = TRUE) ~ 0L,
      grepl("estatut", vd9, ignore.case = TRUE) ~ 0L,
      TRUE ~ NA_integer_
    )
  },
  is_formal = {
    vd9 <- as.character(VD4009)
    v17 <- as.character(V4017)
    inf_tmp <- case_when(
      grepl("privado sem carteira", vd9, ignore.case = TRUE) ~ 1L,
      grepl("stico sem carteira", vd9, ignore.case = TRUE) ~ 1L,
      grepl("familiar auxiliar", vd9, ignore.case = TRUE) ~ 1L,
      grepl("Empregador", vd9, ignore.case = TRUE) &
        grepl("Sim", v17, ignore.case = TRUE) ~ 0L,
      grepl("Empregador", vd9, ignore.case = TRUE) &
        !grepl("Sim", v17, ignore.case = TRUE) ~ 1L,
      grepl("Conta", vd9, ignore.case = TRUE) &
        grepl("Sim", v17, ignore.case = TRUE) ~ 0L,
      grepl("Conta", vd9, ignore.case = TRUE) &
        !grepl("Sim", v17, ignore.case = TRUE) ~ 1L,
      grepl("privado com carteira", vd9, ignore.case = TRUE) ~ 0L,
      grepl("stico com carteira", vd9, ignore.case = TRUE) ~ 0L,
      grepl("blico", vd9, ignore.case = TRUE) ~ 0L,
      grepl("Militar", vd9, ignore.case = TRUE) ~ 0L,
      grepl("estatut", vd9, ignore.case = TRUE) ~ 0L,
      TRUE ~ NA_integer_
    )
    ifelse(inf_tmp == 0L, 1L, 0L)
  },
  hours = as.numeric(V4039),
  hours_bin = case_when(
    as.numeric(V4039) <= 36 ~ "le36",
    as.numeric(V4039) >= 37 & as.numeric(V4039) <= 40 ~ "37_40",
    as.numeric(V4039) >= 41 ~ "ge41",
    TRUE ~ NA_character_
  )
)

# Subset to occupied with valid sector
pnad_occ <- subset(pnad_upd, !is.na(sector))

# -- 4a. Employment shares (lambda_s) --
cat("\n  Employment shares (lambda_s):\n")
emp_total <- svytotal(~factor(sector), pnad_occ, na.rm = TRUE)
emp_df <- data.frame(
  sector = gsub("factor\\(sector\\)", "", names(coef(emp_total))),
  N_thousands = as.numeric(coef(emp_total)) / 1000
)
emp_df$lambda_s <- emp_df$N_thousands / sum(emp_df$N_thousands)
print(emp_df)

# -- 4b. Informality rate by sector --
cat("\n  Informality rate by sector:\n")
inf_by_sector <- svyby(~informal, ~sector, pnad_occ, svymean, na.rm = TRUE)
print(inf_by_sector)
cat("  National informality rate: ",
    round(as.numeric(svymean(~informal, pnad_occ, na.rm = TRUE)) * 100, 1),
    "%\n")

# -- 4c. Average hours by sector (all workers) --
cat("\n  Average hours by sector (all workers):\n")
hours_by_sector <- svyby(~hours, ~sector, pnad_occ, svymean, na.rm = TRUE)
print(hours_by_sector)

# -- 4d. Average hours for formal workers only --
cat("\n  Average hours by sector (formal only):\n")
pnad_formal <- subset(pnad_occ, is_formal == 1)
hours_formal <- svyby(~hours, ~sector, pnad_formal, svymean, na.rm = TRUE)
print(hours_formal)

# -- 4e. Theta_s: hours distribution for formal workers --
cat("\n  Theta_s (hours distribution of formal workers by sector):\n")

theta_results <- list()
for (s in c("agriculture", "industry", "services")) {
  pnad_s <- subset(pnad_formal, sector == s & !is.na(hours_bin))

  theta_s <- svymean(~factor(hours_bin), pnad_s, na.rm = TRUE)
  theta_vec <- as.numeric(coef(theta_s))
  theta_names <- gsub("factor\\(hours_bin\\)", "", names(coef(theta_s)))
  names(theta_vec) <- theta_names

  theta_results[[s]] <- c(
    theta_36 = unname(theta_vec["le36"]),
    theta_40 = unname(theta_vec["37_40"]),
    theta_44 = unname(theta_vec["ge41"])
  )

  cat(sprintf("  %12s: theta_36=%.4f, theta_40=%.4f, theta_44=%.4f (sum=%.4f)\n",
              s, theta_results[[s]]["theta_36"],
              theta_results[[s]]["theta_40"],
              theta_results[[s]]["theta_44"],
              sum(theta_results[[s]])))
}

# -- 4f. National aggregate theta for comparison --
cat("\n  National aggregate theta (formal workers, all sectors):\n")
pnad_formal_all <- subset(pnad_occ, is_formal == 1 & !is.na(hours_bin))
theta_nat <- svymean(~factor(hours_bin), pnad_formal_all, na.rm = TRUE)
theta_nat_vec <- as.numeric(coef(theta_nat))
theta_nat_names <- gsub("factor\\(hours_bin\\)", "", names(coef(theta_nat)))
names(theta_nat_vec) <- theta_nat_names
cat(sprintf("  National: theta_36=%.4f, theta_40=%.4f, theta_44=%.4f\n",
            theta_nat_vec["le36"], theta_nat_vec["37_40"], theta_nat_vec["ge41"]))
cat(sprintf("  DIEESE:   theta_36=0.0850, theta_40=0.2690, theta_44=0.6460\n"))

# -- 5. Save results ---------------------------------------------------------
cat("\n[5] Saving results...\n")

base_dir <- Sys.getenv("JORNADA_BASE_DIR", unset = getwd())
out_dir <- file.path(base_dir, "data_final")

out_df <- data.frame(
  sector = c("agriculture", "industry", "services"),
  stringsAsFactors = FALSE
)

out_df$lambda_s <- emp_df$lambda_s[match(out_df$sector, emp_df$sector)]
out_df$inf_rate <- inf_by_sector$informal[match(out_df$sector,
                                                  inf_by_sector$sector)]
out_df$avg_hours_total <- hours_by_sector$hours[match(out_df$sector,
                                                       hours_by_sector$sector)]
out_df$avg_hours_formal <- hours_formal$hours[match(out_df$sector,
                                                     hours_formal$sector)]

for (s in out_df$sector) {
  out_df$theta_36[out_df$sector == s] <- theta_results[[s]]["theta_36"]
  out_df$theta_40[out_df$sector == s] <- theta_results[[s]]["theta_40"]
  out_df$theta_44[out_df$sector == s] <- theta_results[[s]]["theta_44"]
}

# Add national aggregate row
nat_row <- data.frame(
  sector = "NATIONAL",
  lambda_s = 1.0,
  inf_rate = as.numeric(svymean(~informal, pnad_occ, na.rm = TRUE)),
  avg_hours_total = as.numeric(svymean(~hours, pnad_occ, na.rm = TRUE)),
  avg_hours_formal = as.numeric(svymean(~hours, pnad_formal, na.rm = TRUE)),
  theta_36 = theta_nat_vec["le36"],
  theta_40 = theta_nat_vec["37_40"],
  theta_44 = theta_nat_vec["ge41"],
  stringsAsFactors = FALSE
)

out_df <- rbind(out_df, nat_row)

# Round
out_df$lambda_s <- round(out_df$lambda_s, 4)
out_df$inf_rate <- round(out_df$inf_rate, 4)
out_df$avg_hours_total <- round(out_df$avg_hours_total, 2)
out_df$avg_hours_formal <- round(out_df$avg_hours_formal, 2)
out_df$theta_36 <- round(out_df$theta_36, 4)
out_df$theta_40 <- round(out_df$theta_40, 4)
out_df$theta_44 <- round(out_df$theta_44, 4)

out_path <- file.path(out_dir, "SECTORAL_PNAD_EMPIRICAL.csv")
write.csv(out_df, out_path, row.names = FALSE)
cat("  Saved:", out_path, "\n")

# -- 6. Print comparison with estimates ---------------------------------------
cat("\n", rep("=", 70), "\n", sep = "")
cat("COMPARISON: Estimated vs Empirical (PNAD microdata)\n")
cat(rep("=", 70), "\n", sep = "")

estimated <- data.frame(
  sector = c("agriculture", "industry", "services"),
  est_lambda = c(0.085, 0.203, 0.712),
  est_inf = c(0.607, 0.228, 0.371),
  est_theta_36 = c(0.040, 0.050, 0.100),
  est_theta_40 = c(0.180, 0.300, 0.260),
  est_theta_44 = c(0.780, 0.650, 0.640)
)

comp <- merge(out_df[out_df$sector != "NATIONAL", ], estimated, by = "sector")

cat("\n  EMPLOYMENT SHARES (lambda_s):\n")
for (i in 1:nrow(comp)) {
  cat(sprintf("    %12s: estimated=%.3f, empirical=%.3f, diff=%+.3f\n",
              comp$sector[i], comp$est_lambda[i], comp$lambda_s[i],
              comp$lambda_s[i] - comp$est_lambda[i]))
}

cat("\n  INFORMALITY RATE:\n")
for (i in 1:nrow(comp)) {
  cat(sprintf("    %12s: estimated=%.1f%%, empirical=%.1f%%, diff=%+.1fpp\n",
              comp$sector[i], comp$est_inf[i]*100, comp$inf_rate[i]*100,
              (comp$inf_rate[i] - comp$est_inf[i])*100))
}

cat("\n  THETA_36 (share of formal workers <= 36h):\n")
for (i in 1:nrow(comp)) {
  cat(sprintf("    %12s: estimated=%.3f, empirical=%.3f, diff=%+.3f\n",
              comp$sector[i], comp$est_theta_36[i], comp$theta_36[i],
              comp$theta_36[i] - comp$est_theta_36[i]))
}

cat("\n  THETA_40 (share of formal workers 37-40h):\n")
for (i in 1:nrow(comp)) {
  cat(sprintf("    %12s: estimated=%.3f, empirical=%.3f, diff=%+.3f\n",
              comp$sector[i], comp$est_theta_40[i], comp$theta_40[i],
              comp$theta_40[i] - comp$est_theta_40[i]))
}

cat("\n  THETA_44 (share of formal workers >= 41h):\n")
for (i in 1:nrow(comp)) {
  cat(sprintf("    %12s: estimated=%.3f, empirical=%.3f, diff=%+.3f\n",
              comp$sector[i], comp$est_theta_44[i], comp$theta_44[i],
              comp$theta_44[i] - comp$est_theta_44[i]))
}

cat("\nDONE.\n")

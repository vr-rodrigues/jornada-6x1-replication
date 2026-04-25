library(PNADcIBGE)
cat("Downloading PNAD Q4 2024...\n")
pnad <- get_pnadc(year = 2024, quarter = 4)
df <- pnad$variables

cat("\n=== All V40xx variables ===\n")
v40_vars <- grep("^V40[0-9]", names(df), value = TRUE)
cat(paste(v40_vars, collapse = ", "), "\n")

cat("\n=== V4017 ===\n")
if ("V4017" %in% names(df)) {
  print(table(df$V4017, useNA = "ifany"))
} else {
  cat("NOT FOUND\n")
}

cat("\n=== V4018 ===\n")
if ("V4018" %in% names(df)) {
  print(table(df$V4018, useNA = "ifany"))
} else {
  cat("NOT FOUND\n")
}

cat("\n=== V4019 ===\n")
if ("V4019" %in% names(df)) {
  print(table(df$V4019, useNA = "ifany"))
} else {
  cat("NOT FOUND\n")
}

cat("\n=== VD4010 ===\n")
if ("VD4010" %in% names(df)) {
  print(table(df$VD4010, useNA = "ifany"))
} else {
  cat("NOT FOUND\n")
}

cat("\n=== VD4012 ===\n")
if ("VD4012" %in% names(df)) {
  print(table(df$VD4012, useNA = "ifany"))
} else {
  cat("NOT FOUND\n")
}

# Cross-tab VD4009 x V4017 for Conta-propria and Empregador
cat("\n=== V4017 x VD4009 for Conta-propria ===\n")
cp <- df[grepl("Conta", as.character(df$VD4009), ignore.case = TRUE), ]
if ("V4017" %in% names(df)) {
  print(table(cp$V4017, useNA = "ifany"))
}

cat("\n=== V4019 x VD4009 for Empregador ===\n")
emp <- df[grepl("Empregador", as.character(df$VD4009), ignore.case = TRUE), ]
if ("V4019" %in% names(df)) {
  print(table(emp$V4019, useNA = "ifany"))
}

cat("\nDONE\n")

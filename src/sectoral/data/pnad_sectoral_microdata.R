# One canonical implementation: V4019 is CNPJ, V4017 is presence of a partner.
# Required quarter: 2024Q4. Habitual/actual hours are never called contracted.
# BigQuery is tried first; any official IBGE fallback keeps the same quarter and
# is recorded in the provenance manifest. Original inputs are never overwritten.
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
if (length(file_arg) != 1L) stop("Run this file with Rscript.")
script <- normalizePath(sub("^--file=", "", file_arg))
root <- normalizePath(file.path(dirname(script), "..", "..", ".."))
python <- Sys.getenv("JORNADA_PYTHON", Sys.which("python"))
if (!nzchar(python)) stop("Python missing; set JORNADA_PYTHON.")
collector <- file.path(root, "src", "data_raw", "reprocess_verified_inputs.py")
status <- system2(python, c(shQuote(collector), "--project",
    shQuote(Sys.getenv("GCP_BILLING_PROJECT", "upa-research")),
    "--allow-official-fallback"))
if (status != 0L) stop("PNAD 2024Q4 failed; old output is not substituted.")
cat("Verified national/sectoral PNAD aggregates are in the reprocessed folders.\n")

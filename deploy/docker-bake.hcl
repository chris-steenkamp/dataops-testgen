variable "TESTGEN_LABELS" {}
variable "TESTGEN_BASE_LABEL" {}
variable "TESTGEN_VERSION" {}

target "testgen-release" {
  args = {
    TESTGEN_VERSION = "${TESTGEN_VERSION}"
    TESTGEN_BASE_LABEL = "${TESTGEN_BASE_LABEL}"
  }
  context = "."
  dockerfile = "deploy/testgen.dockerfile"
  platforms = ["linux/amd64", "linux/arm64"]
  tags = formatlist("datakitchen/dataops-testgen:%s", split(" ", TESTGEN_LABELS))
}

target "testgen-qa" {
  args = {
    TESTGEN_VERSION = "${TESTGEN_VERSION}"
    TESTGEN_BASE_LABEL = "${TESTGEN_BASE_LABEL}"
  }
  context = "."
  dockerfile = "deploy/testgen.dockerfile"
  platforms = ["linux/amd64", "linux/arm64"]
  tags = [format("datakitchen/dataops-testgen-qa:%s", index(split(" ", TESTGEN_LABELS), 0))]
}

target "testgen-base" {
  context = "."
  dockerfile = "deploy/testgen-base.dockerfile"
  platforms = ["linux/amd64", "linux/arm64"]
  tags = formatlist("datakitchen/dataops-testgen-base:%s", split(" ", TESTGEN_LABELS))
}

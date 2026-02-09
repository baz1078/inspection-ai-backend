-- CreateTable
CREATE TABLE "WarrantyDocument" (
    "id" TEXT NOT NULL,
    "builderName" TEXT NOT NULL,
    "warrantyType" TEXT NOT NULL,
    "jurisdiction" TEXT NOT NULL,
    "filePath" TEXT NOT NULL,
    "originalFilename" TEXT NOT NULL,
    "fileSize" INTEGER NOT NULL,
    "extractedText" TEXT NOT NULL,
    "coverageRules" TEXT NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "WarrantyDocument_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ReportWarranty" (
    "id" TEXT NOT NULL,
    "reportId" TEXT NOT NULL,
    "warrantyId" TEXT NOT NULL,
    "certificateNumber" TEXT,
    "warrantyStartDate" TIMESTAMP(3),
    "warrantyEndDate" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ReportWarranty_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "WarrantyQuery" (
    "id" TEXT NOT NULL,
    "reportId" TEXT NOT NULL,
    "warrantyId" TEXT NOT NULL,
    "customerQuestion" TEXT NOT NULL,
    "inspectionFinding" TEXT NOT NULL,
    "claimability" TEXT NOT NULL,
    "claimReason" TEXT NOT NULL,
    "warranty_section" TEXT,
    "ai_analysis" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "WarrantyQuery_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DamageAssessmentReport" (
    "id" TEXT NOT NULL,
    "customerName" TEXT NOT NULL,
    "customerEmail" TEXT NOT NULL,
    "customerPhone" TEXT NOT NULL,
    "damageLocation" TEXT NOT NULL,
    "waterSource" TEXT,
    "damageDescription" TEXT,
    "photoPath" TEXT NOT NULL,
    "pdfPath" TEXT NOT NULL,
    "moldRiskPercentage" INTEGER NOT NULL,
    "claimApprovalPercentage" INTEGER NOT NULL,
    "damageSeverity" TEXT NOT NULL,
    "estimatedSquareFootage" INTEGER,
    "moistureSaturation" TEXT,
    "affectedMaterials" TEXT NOT NULL,
    "visibleIssues" TEXT NOT NULL,
    "hiddenDamageRisk" TEXT,
    "recommendedAction" TEXT,
    "structuralRisk" TEXT,
    "shareToken" TEXT NOT NULL,
    "isShared" BOOLEAN NOT NULL DEFAULT true,
    "publicLink" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "DamageAssessmentReport_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "WarrantyDocument_builderName_idx" ON "WarrantyDocument"("builderName");

-- CreateIndex
CREATE INDEX "WarrantyDocument_warrantyType_idx" ON "WarrantyDocument"("warrantyType");

-- CreateIndex
CREATE INDEX "WarrantyDocument_jurisdiction_idx" ON "WarrantyDocument"("jurisdiction");

-- CreateIndex
CREATE INDEX "ReportWarranty_reportId_idx" ON "ReportWarranty"("reportId");

-- CreateIndex
CREATE INDEX "ReportWarranty_warrantyId_idx" ON "ReportWarranty"("warrantyId");

-- CreateIndex
CREATE UNIQUE INDEX "ReportWarranty_reportId_warrantyId_key" ON "ReportWarranty"("reportId", "warrantyId");

-- CreateIndex
CREATE INDEX "WarrantyQuery_reportId_idx" ON "WarrantyQuery"("reportId");

-- CreateIndex
CREATE INDEX "WarrantyQuery_warrantyId_idx" ON "WarrantyQuery"("warrantyId");

-- CreateIndex
CREATE INDEX "WarrantyQuery_claimability_idx" ON "WarrantyQuery"("claimability");

-- CreateIndex
CREATE UNIQUE INDEX "DamageAssessmentReport_shareToken_key" ON "DamageAssessmentReport"("shareToken");

-- CreateIndex
CREATE INDEX "DamageAssessmentReport_shareToken_idx" ON "DamageAssessmentReport"("shareToken");

-- CreateIndex
CREATE INDEX "DamageAssessmentReport_createdAt_idx" ON "DamageAssessmentReport"("createdAt");

-- CreateIndex
CREATE INDEX "DamageAssessmentReport_damageLocation_idx" ON "DamageAssessmentReport"("damageLocation");

-- AddForeignKey
ALTER TABLE "ReportWarranty" ADD CONSTRAINT "ReportWarranty_reportId_fkey" FOREIGN KEY ("reportId") REFERENCES "InspectionReport"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ReportWarranty" ADD CONSTRAINT "ReportWarranty_warrantyId_fkey" FOREIGN KEY ("warrantyId") REFERENCES "WarrantyDocument"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "WarrantyQuery" ADD CONSTRAINT "WarrantyQuery_reportId_fkey" FOREIGN KEY ("reportId") REFERENCES "InspectionReport"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "WarrantyQuery" ADD CONSTRAINT "WarrantyQuery_warrantyId_fkey" FOREIGN KEY ("warrantyId") REFERENCES "WarrantyDocument"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

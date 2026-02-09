/*
  Warnings:

  - You are about to drop the column `ai_analysis` on the `WarrantyQuery` table. All the data in the column will be lost.
  - You are about to drop the column `warranty_section` on the `WarrantyQuery` table. All the data in the column will be lost.
  - You are about to drop the `DamageAssessmentReport` table. If the table is not empty, all the data it contains will be lost.
  - Added the required column `aiAnalysis` to the `WarrantyQuery` table without a default value. This is not possible if the table is not empty.

*/
-- DropForeignKey
ALTER TABLE "WarrantyQuery" DROP CONSTRAINT "WarrantyQuery_warrantyId_fkey";

-- DropIndex
DROP INDEX "WarrantyQuery_warrantyId_idx";

-- AlterTable
ALTER TABLE "WarrantyQuery" DROP COLUMN "ai_analysis",
DROP COLUMN "warranty_section",
ADD COLUMN     "aiAnalysis" TEXT NOT NULL,
ADD COLUMN     "warrantySection" TEXT,
ALTER COLUMN "claimability" DROP NOT NULL;

-- DropTable
DROP TABLE "DamageAssessmentReport";

-- AddForeignKey
ALTER TABLE "WarrantyQuery" ADD CONSTRAINT "WarrantyQuery_warrantyId_fkey" FOREIGN KEY ("warrantyId") REFERENCES "WarrantyDocument"("id") ON DELETE CASCADE ON UPDATE CASCADE;

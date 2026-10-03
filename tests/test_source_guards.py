from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
FINAL_DAO = "0x928Afe4a4d0978206bD7311548998f0BB1E89230"


class SourceGuards(unittest.TestCase):
    def test_equal_holder_not_balance_weighted(self):
        source = (ROOT / "04-token/LaborCoinV4.sol").read_text()
        for marker in [
            "eligibleDividendHolderCount",
            "magnifiedDividendPerEligibleHolder",
            "dividendEligible",
            "claimDividends",
            "MIN_DIVIDEND_BALANCE",
        ]:
            self.assertIn(marker, source)
        self.assertNotIn("magnifiedDividendPerShare * eligibleBalance", source)
        self.assertNotRegex(
            source, r"msg\.value\s*\*\s*MAGNITUDE\s*\)\s*/\s*totalDividendEligibleSupply"
        )

    def test_identity_gates(self):
        token = (ROOT / "04-token/LaborCoinV4.sol").read_text()
        exchange = (ROOT / "03-exchange/LaborCoinExchangeV7.sol").read_text()
        self.assertIn("IdentityVerificationRequired", token)
        self.assertGreaterEqual(exchange.count("_requireVerified(msg.sender)"), 2)
        self.assertIn("claimDividends", token)

    def test_protocol_only_transfer_policy(self):
        token = (ROOT / "04-token/LaborCoinV4.sol").read_text()
        self.assertIn("error PeerTransfersDisabled();", token)
        self.assertIn(
            "if (msg.sender != officialExchange) revert UnauthorizedTransferOperator(msg.sender);",
            token,
        )
        self.assertIn(
            "if (msg.sender != exchange) revert DirectExchangeTransferForbidden();", token
        )
        self.assertIn("revert PeerTransfersDisabled();", token)
        self.assertNotIn("_requireStrictWallet", token)

    def test_permanent_limits(self):
        exchange = (ROOT / "03-exchange/LaborCoinExchangeV7.sol").read_text()
        identity = (ROOT / "02-identity-registry/LaborCoinIdentityRegistryV1.sol").read_text()
        for marker in ["10_000 ether", "5_000 ether", "12 hours"]:
            self.assertIn(marker, exchange)
        self.assertIn("15_000", identity)

    def test_deadline_electorate_policy(self):
        registration = (ROOT / "06-registration/LaborCoinRegistrationV6.sol").read_text()
        governance = (ROOT / "07-governance/LaborCoinGovernanceV16.sol").read_text()
        self.assertIn("registrationTimestampByMemberNumber", registration)
        self.assertIn("totalMembersBefore(uint256 timestampExclusive)", registration)
        self.assertIn("registeredAt >= proposal.endTime", governance)
        self.assertIn("totalMembersBefore(proposal.endTime)", governance)
        self.assertNotIn("MemberJoinedAfterSnapshot", governance)

    def test_final_dao_bindings(self):
        exchange = (ROOT / "03-exchange/LaborCoinExchangeV7.sol").read_text()
        token = (ROOT / "04-token/LaborCoinV4.sol").read_text()
        governance = (ROOT / "07-governance/LaborCoinGovernanceV16.sol").read_text()
        self.assertIn(FINAL_DAO, exchange)
        self.assertIn(FINAL_DAO, token)
        self.assertIn(FINAL_DAO, governance)

    def test_governance_v16_multi_asset_guards(self):
        governance = (ROOT / "07-governance/LaborCoinGovernanceV16.sol").read_text()
        for marker in [
            "LABORCOIN_STRUCTURED_TREASURY_PROPOSAL_SCHEMA_V2_MULTI_ASSET",
            "LaborCoin Structured Treasury Proposal Schema V2",
            "assetBalanceSnapshot",
            "Math.mulDiv",
            "function assetBalance(",
            "function maxProposalAmount(",
            "_ERC20_BALANCE_OF_SELECTOR",
            "_ERC20_TRANSFER_SELECTOR",
            "ERC20TransferReturnedFalse",
            "InvalidERC20TransferReturnData",
            "InvalidERC20TransferReturnValue",
            "ERC20TreasuryBalanceDeltaMismatch",
            "ERC20RecipientBalanceDeltaMismatch",
            "ERC20NativeBalanceChanged",
            "NativeTreasuryBalanceDeltaMismatch",
            "ProtectedProtocolAsset",
            "AssetEqualsRecipient",
            "return abi.decode(data, (uint256));",
            "FINAL_BOOTSTRAP_ADMIN_PLUGIN",
            "new IAragonDAOForGovernance.Action[](1)",
        ]:
            self.assertIn(marker, governance)
        self.assertGreaterEqual(governance.count("Math.mulDiv"), 2)
        self.assertNotIn("LaborCoinGovernanceV15", governance)

    def test_governance_fixed_proposal_schema(self):
        governance = (ROOT / "07-governance/LaborCoinGovernanceV16.sol").read_text()
        match = re.search(r"struct\s+ProposalInput\s*\{(.*?)\}", governance, re.DOTALL)
        self.assertIsNotNone(match)
        body = match.group(1)
        expected_fields = [
            ("string", "organizationName"),
            ("address", "asset"),
            ("address", "recipient"),
            ("string", "workerGroupOrCampaign"),
            ("uint256", "amount"),
            ("Purpose", "purpose"),
            ("string", "verificationURI"),
            ("ContactMethod", "contactMethod"),
            ("DistributionPlan", "distributionPlan"),
        ]
        actual_fields = re.findall(
            r"\b(string|address|uint256|Purpose|ContactMethod|DistributionPlan)\s+"
            r"([A-Za-z_][A-Za-z0-9_]*)\s*;",
            body,
        )
        self.assertEqual(actual_fields, expected_fields)
        self.assertNotRegex(body, r"\bbytes(?:\d*)?\b")
        self.assertNotIn("Action", body)

    def test_versions(self):
        expected = {
            "01-policy": "V1.1.1",
            "02-identity-registry": "V1.0.1",
            "03-exchange": "V7.1.0",
            "04-token": "V4.1.0",
            "05-labrv": "V9.1.1",
            "06-registration": "V6.1.1",
            "07-governance": "V16.0.0",
        }
        manifest = json.loads((ROOT / "MASTER_COMPILATION_MANIFEST.json").read_text())
        for entry in manifest["contracts"]:
            self.assertIn(expected[entry["folder"]], entry["version"])


if __name__ == "__main__":
    unittest.main()

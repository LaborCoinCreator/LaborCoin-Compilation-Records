from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

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
            source,
            r"msg\.value\s*\*\s*MAGNITUDE\s*\)\s*/\s*totalDividendEligibleSupply",
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
        self.assertIn("if (msg.sender != officialExchange) revert UnauthorizedTransferOperator(msg.sender);", token)
        self.assertIn("if (msg.sender != exchange) revert DirectExchangeTransferForbidden();", token)
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
        governance = (ROOT / "07-governance/LaborCoinGovernanceV15.sol").read_text()
        self.assertIn("registrationTimestampByMemberNumber", registration)
        self.assertIn("totalMembersBefore(uint256 timestampExclusive)", registration)
        self.assertIn("registeredAt >= proposal.endTime", governance)
        self.assertIn("totalMembersBefore(proposal.endTime)", governance)
        self.assertNotIn("MemberJoinedAfterSnapshot", governance)

    def test_versions(self):
        expected = {
            "01-policy": "V1.0.1",
            "02-identity-registry": "V1.0.1",
            "03-exchange": "V7.0.0",
            "04-token": "V4.0.0",
            "05-labrv": "V9.1.1",
            "06-registration": "V6.1.1",
            "07-governance": "V15.1.1",
        }
        manifest = json.loads((ROOT / "MASTER_COMPILATION_MANIFEST.json").read_text())
        for entry in manifest["contracts"]:
            self.assertIn(expected[entry["folder"]], entry["version"])

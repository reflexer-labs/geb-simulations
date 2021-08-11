/// PIRawPerSecondCalculator.sol

/**
Reflexer PI Controller License 1.0

Definitions

Primary License: This license agreement
Secondary License: GNU General Public License v2.0 or later
Effective Date of Secondary License: May 5, 2023

Licensed Software:

Software License Grant: Subject to and dependent upon your adherence to the terms and conditions of this Primary License, and subject to explicit approval by Reflexer, Inc., Reflexer, Inc., hereby grants you the right to copy, modify or otherwise create derivative works, redistribute, and use the Licensed Software solely for internal testing and development, and solely until the Effective Date of the Secondary License.  You may not, and you agree you will not, use the Licensed Software outside the scope of the limited license grant in this Primary License.

You agree you will not (i) use the Licensed Software for any commercial purpose, and (ii) deploy the Licensed Software to a blockchain system other than as a noncommercial deployment to a testnet in which tokens or transactions could not reasonably be expected to have or develop commercial value.You agree to be bound by the terms and conditions of this Primary License until the Effective Date of the Secondary License, at which time the Primary License will expire and be replaced by the Secondary License. You Agree that as of the Effective Date of the Secondary License, you will be bound by the terms and conditions of the Secondary License.
You understand and agree that any violation of the terms and conditions of this License will automatically terminate your rights under this License for the current and all other versions of the Licensed Software.
You understand and agree that any use of the Licensed Software outside the boundaries of the limited licensed granted in this Primary License renders the license granted in this Primary License null and void as of the date you first used the Licensed Software in any way (void ab initio).You understand and agree that you may purchase a commercial license to use a version of the Licensed Software under the terms and conditions set by Reflexer, Inc.  You understand and agree that you will display an unmodified copy of this Primary License with each Licensed Software, and any derivative work of the Licensed Software.

TO THE EXTENT PERMITTED BY APPLICABLE LAW, THE LICENSED SOFTWARE IS PROVIDED ON AN “AS IS” BASIS. REFLEXER, INC HEREBY DISCLAIMS ALL WARRANTIES AND CONDITIONS, EXPRESS OR IMPLIED, INCLUDING (WITHOUT LIMITATION) ANY WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, AND TITLE.
You understand and agree that all copies of the Licensed Software, and all derivative works thereof, are each subject to the terms and conditions of this License. Notwithstanding the foregoing, You hereby grant to Reflexer, Inc. a fully paid-up, worldwide, fully sublicensable license to use,for any lawful purpose, any such derivative work made by or for You, now or in the future. You agree that you will, at the request of Reflexer, Inc., provide Reflexer, Inc. with the complete source code to such derivative work.

Copyright © 2021 Reflexer Inc. All Rights Reserved
**/

pragma solidity ^0.6.7;

import "../../math/SafeMath.sol";
import "../../math/SignedSafeMath.sol";

contract PIRawPerSecondCalculator is SafeMath, SignedSafeMath {
    // --- Authorities ---
    mapping (address => uint) public authorities;
    function addAuthority(address account) external isAuthority { authorities[account] = 1; }
    function removeAuthority(address account) external isAuthority { authorities[account] = 0; }
    modifier isAuthority {
        require(authorities[msg.sender] == 1, "PIRawPerSecondCalculator/not-an-authority");
        _;
    }

    // --- Readers ---
    mapping (address => uint) public readers;
    function addReader(address account) external isAuthority { readers[account] = 1; }
    function removeReader(address account) external isAuthority { readers[account] = 0; }
    modifier isReader {
        require(either(allReaderToggle == 1, readers[msg.sender] == 1), "PIRawPerSecondCalculator/not-a-reader");
        _;
    }

    // --- Structs ---
    struct ControllerGains {
        int Kp;                                      // [EIGHTEEN_DECIMAL_NUMBER]
        int Ki;                                      // [EIGHTEEN_DECIMAL_NUMBER]
    }
    struct DeviationObservation {
        uint timestamp;
        int  proportional;
        int  integral;
    }

    // -- Static & Default Variables ---
    ControllerGains internal controllerGains;

    uint256 public   allReaderToggle;
    uint256 internal noiseBarrier;                   // [EIGHTEEN_DECIMAL_NUMBER]
    uint256 internal defaultRedemptionRate;          // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal feedbackOutputUpperBound;       // [TWENTY_SEVEN_DECIMAL_NUMBER]
    int256  internal feedbackOutputLowerBound;       // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal integralPeriodSize;             // [seconds]

    // --- Fluctuating/Dynamic Variables ---
    DeviationObservation[] internal deviationObservations;
    int256[]               internal historicalCumulativeDeviations;

    int256  internal priceDeviationCumulative;             // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal perSecondCumulativeLeak;              // [TWENTY_SEVEN_DECIMAL_NUMBER]
    uint256 internal lastUpdateTime;                       // [timestamp]
    uint256 constant internal defaultGlobalTimeline = 1;

    address public seedProposer;

    uint256 internal constant NEGATIVE_RATE_LIMIT         = TWENTY_SEVEN_DECIMAL_NUMBER - 1;
    uint256 internal constant TWENTY_SEVEN_DECIMAL_NUMBER = 10 ** 27;
    uint256 internal constant EIGHTEEN_DECIMAL_NUMBER     = 10 ** 18;

    constructor(
        int256 Kp_,
        int256 Ki_,
        uint256 perSecondCumulativeLeak_,
        uint256 integralPeriodSize_,
        uint256 noiseBarrier_,
        uint256 feedbackOutputUpperBound_,
        int256  feedbackOutputLowerBound_,
        int256[] memory importedState
    ) public {
        defaultRedemptionRate           = TWENTY_SEVEN_DECIMAL_NUMBER;
        require(both(feedbackOutputUpperBound_ < subtract(subtract(uint(-1), defaultRedemptionRate), 1), feedbackOutputUpperBound_ > 0), "PIRawPerSecondCalculator/invalid-foub");
        require(both(feedbackOutputLowerBound_ < 0, feedbackOutputLowerBound_ >= -int(NEGATIVE_RATE_LIMIT)), "PIRawPerSecondCalculator/invalid-folb");
        require(integralPeriodSize_ > 0, "PIRawPerSecondCalculator/invalid-ips");
        require(uint(importedState[0]) <= now, "PIRawPerSecondCalculator/invalid-imported-time");
        require(noiseBarrier_ <= EIGHTEEN_DECIMAL_NUMBER, "PIRawPerSecondCalculator/invalid-nb");
        authorities[msg.sender]         = 1;
        readers[msg.sender]             = 1;
        feedbackOutputUpperBound        = feedbackOutputUpperBound_;
        feedbackOutputLowerBound        = feedbackOutputLowerBound_;
        integralPeriodSize              = integralPeriodSize_;
        controllerGains                 = ControllerGains(Kp_, Ki_);
        perSecondCumulativeLeak         = perSecondCumulativeLeak_;
        priceDeviationCumulative        = importedState[3];
        noiseBarrier                    = noiseBarrier_;
        lastUpdateTime                  = uint(importedState[0]);
        if (importedState[4] > 0) {
          deviationObservations.push(
            DeviationObservation(uint(importedState[4]), importedState[1], importedState[2])
          );
        }
        historicalCumulativeDeviations.push(priceDeviationCumulative);
    }

    // --- Boolean Logic ---
    function both(bool x, bool y) internal pure returns (bool z) {
        assembly{ z := and(x, y)}
    }
    function either(bool x, bool y) internal pure returns (bool z) {
        assembly{ z := or(x, y)}
    }

    // --- Administration ---
    function modifyParameters(bytes32 parameter, address addr) external isAuthority {
        if (parameter == "seedProposer") {
          readers[seedProposer] = 0;
          seedProposer = addr;
          readers[seedProposer] = 1;
        }
        else revert("PIRawPerSecondCalculator/modify-unrecognized-param");
    }
    function modifyParameters(bytes32 parameter, uint256 val) external isAuthority {
        if (parameter == "nb") {
          require(val <= EIGHTEEN_DECIMAL_NUMBER, "PIRawPerSecondCalculator/invalid-nb");
          noiseBarrier = val;
        }
        else if (parameter == "ips") {
          require(val > 0, "PIRawPerSecondCalculator/null-ips");
          integralPeriodSize = val;
        }
        else if (parameter == "foub") {
          require(both(val < subtract(subtract(uint(-1), defaultRedemptionRate), 1), val > 0), "PIRawPerSecondCalculator/invalid-foub");
          feedbackOutputUpperBound = val;
        }
        else if (parameter == "pscl") {
          require(val <= TWENTY_SEVEN_DECIMAL_NUMBER, "PIRawPerSecondCalculator/invalid-pscl");
          perSecondCumulativeLeak = val;
        }
        else if (parameter == "allReaderToggle") {
          allReaderToggle = val;
        }
        else revert("PIRawPerSecondCalculator/modify-unrecognized-param");
    }
    function modifyParameters(bytes32 parameter, int256 val) external isAuthority {
        if (parameter == "folb") {
          require(both(val < 0, val >= -int(NEGATIVE_RATE_LIMIT)), "PIRawPerSecondCalculator/invalid-folb");
          feedbackOutputLowerBound = val;
        }
        else if (parameter == "sg") {
          controllerGains.Kp = val;
        }
        else if (parameter == "ag") {
          controllerGains.Ki = val;
        }
        else if (parameter == "pdc") {
          require(controllerGains.Ki == 0, "PIRawPerSecondCalculator/cannot-set-pdc");
          priceDeviationCumulative = val;
        }
        else revert("PIRawPerSecondCalculator/modify-unrecognized-param");
    }

    // --- PI Specific Math ---
    function riemannSum(int x, int y) internal pure returns (int z) {
        return addition(x, y) / 2;
    }
    function absolute(int x) internal pure returns (uint z) {
        z = (x < 0) ? uint(-x) : uint(x);
    }

    // --- PI Utils ---
    function getLastProportionalTerm() public isReader view returns (int256) {
        if (oll() == 0) return 0;
        return deviationObservations[oll() - 1].proportional;
    }
    function getLastIntegralTerm() public isReader view returns (int256) {
        if (oll() == 0) return 0;
        return deviationObservations[oll() - 1].integral;
    }
    function oll() public isReader view returns (uint256) {
        return deviationObservations.length;
    }
    function getBoundedRedemptionRate(int piOutput) public isReader view returns (uint256, uint256) {
        int  boundedPIOutput = piOutput;
        uint newRedemptionRate;

        if (piOutput < feedbackOutputLowerBound) {
          boundedPIOutput = feedbackOutputLowerBound;
        } else if (piOutput > int(feedbackOutputUpperBound)) {
          boundedPIOutput = int(feedbackOutputUpperBound);
        }

        bool negativeOutputExceedsHundred = (boundedPIOutput < 0 && -boundedPIOutput >= int(defaultRedemptionRate));
        if (negativeOutputExceedsHundred) {
          newRedemptionRate = NEGATIVE_RATE_LIMIT;
        } else {
          if (boundedPIOutput < 0 && boundedPIOutput <= -int(NEGATIVE_RATE_LIMIT)) {
            newRedemptionRate = uint(addition(int(defaultRedemptionRate), -int(NEGATIVE_RATE_LIMIT)));
          } else {
            newRedemptionRate = uint(addition(int(defaultRedemptionRate), boundedPIOutput));
          }
        }

        return (newRedemptionRate, defaultGlobalTimeline);
    }
    function breaksNoiseBarrier(uint piSum, uint redemptionPrice) public isReader view returns (bool) {
        uint deltaNoise = subtract(multiply(uint(2), EIGHTEEN_DECIMAL_NUMBER), noiseBarrier);
        return piSum >= subtract(divide(multiply(redemptionPrice, deltaNoise), EIGHTEEN_DECIMAL_NUMBER), redemptionPrice);
    }
    function getNextPriceDeviationCumulative(int proportionalTerm, uint accumulatedLeak) public isReader view returns (int256, int256) {
        int256 lastProportionalTerm      = getLastProportionalTerm();
        uint256 timeElapsed              = (lastUpdateTime == 0) ? 0 : subtract(now, lastUpdateTime);
        int256 newTimeAdjustedDeviation  = multiply(riemannSum(proportionalTerm, lastProportionalTerm), int(timeElapsed));
        int256 leakedPriceCumulative     = divide(multiply(int(accumulatedLeak), priceDeviationCumulative), int(TWENTY_SEVEN_DECIMAL_NUMBER));

        return (
          addition(leakedPriceCumulative, newTimeAdjustedDeviation),
          newTimeAdjustedDeviation
        );
    }
    function getGainAdjustedPIOutput(int proportionalTerm, int integralTerm) public isReader view returns (int256) {
        (int adjustedProportional, int adjustedIntegral) = getGainAdjustedTerms(proportionalTerm, integralTerm);
        return addition(adjustedProportional, adjustedIntegral);
    }
    function getGainAdjustedTerms(int proportionalTerm, int integralTerm) public isReader view returns (int256, int256) {
        return (
          multiply(proportionalTerm, int(controllerGains.Kp)) / int(EIGHTEEN_DECIMAL_NUMBER),
          multiply(integralTerm, int(controllerGains.Ki)) / int(EIGHTEEN_DECIMAL_NUMBER)
        );
    }

    // --- Rate Validation/Calculation ---
    function computeRate(
      uint marketPrice,
      uint redemptionPrice,
      uint accumulatedLeak
    ) external returns (uint256) {
        require(seedProposer == msg.sender, "PIRawPerSecondCalculator/invalid-msg-sender");
        require(subtract(now, lastUpdateTime) >= integralPeriodSize || lastUpdateTime == 0, "PIRawPerSecondCalculator/wait-more");
        int256 proportionalTerm = subtract(int(redemptionPrice), multiply(int(marketPrice), int(10**9)));
        updateDeviationHistory(proportionalTerm, accumulatedLeak);
        lastUpdateTime = now;
        int256 piOutput = getGainAdjustedPIOutput(proportionalTerm, priceDeviationCumulative);
        if (
          breaksNoiseBarrier(absolute(piOutput), redemptionPrice) &&
          piOutput != 0
        ) {
          (uint newRedemptionRate, ) = getBoundedRedemptionRate(piOutput);
          return newRedemptionRate;
        } else {
          return TWENTY_SEVEN_DECIMAL_NUMBER;
        }
    }
    function updateDeviationHistory(int proportionalTerm, uint accumulatedLeak) internal {
        (int256 virtualDeviationCumulative, int256 nextTimeAdjustedDeviation) =
          getNextPriceDeviationCumulative(proportionalTerm, accumulatedLeak);
        priceDeviationCumulative = virtualDeviationCumulative;
        historicalCumulativeDeviations.push(priceDeviationCumulative);
        deviationObservations.push(DeviationObservation(now, proportionalTerm, priceDeviationCumulative));
    }
    function getNextRedemptionRate(uint marketPrice, uint redemptionPrice, uint accumulatedLeak)
      public isReader view returns (uint256, int256, int256, uint256) {
        int256 proportionalTerm = subtract(int(redemptionPrice), multiply(int(marketPrice), int(10**9)));
        (int cumulativeDeviation, ) = getNextPriceDeviationCumulative(proportionalTerm, accumulatedLeak);
        int piOutput = getGainAdjustedPIOutput(proportionalTerm, cumulativeDeviation);
        if (
          breaksNoiseBarrier(absolute(piOutput), redemptionPrice) &&
          piOutput != 0
        ) {
          (uint newRedemptionRate, uint rateTimeline) = getBoundedRedemptionRate(piOutput);
          return (newRedemptionRate, proportionalTerm, cumulativeDeviation, rateTimeline);
        } else {
          return (TWENTY_SEVEN_DECIMAL_NUMBER, proportionalTerm, cumulativeDeviation, defaultGlobalTimeline);
        }
    }

    // --- Parameter Getters ---
    function rt(uint marketPrice, uint redemptionPrice, uint accumulatedLeak) external isReader view returns (uint256) {
        (, , , uint rateTimeline) = getNextRedemptionRate(marketPrice, redemptionPrice, accumulatedLeak);
        return rateTimeline;
    }
    function sg() external isReader view returns (int256) {
        return controllerGains.Kp;
    }
    function ag() external isReader view returns (int256) {
        return controllerGains.Ki;
    }
    function nb() external isReader view returns (uint256) {
        return noiseBarrier;
    }
    function drr() external isReader view returns (uint256) {
        return defaultRedemptionRate;
    }
    function foub() external isReader view returns (uint256) {
        return feedbackOutputUpperBound;
    }
    function folb() external isReader view returns (int256) {
        return feedbackOutputLowerBound;
    }
    function ips() external isReader view returns (uint256) {
        return integralPeriodSize;
    }
    function dos(uint256 i) external isReader view returns (uint256, int256, int256) {
        return (deviationObservations[i].timestamp, deviationObservations[i].proportional, deviationObservations[i].integral);
    }
    function hcd(uint256 i) external isReader view returns (int256) {
        return historicalCumulativeDeviations[i];
    }
    function pdc() external isReader view returns (int256) {
        return priceDeviationCumulative;
    }
    function pscl() external isReader view returns (uint256) {
        return perSecondCumulativeLeak;
    }
    function lprad() external isReader view returns (uint256) {
        return 1;
    }
    function uprad() external isReader view returns (uint256) {
        return uint(-1);
    }
    function adi() external isReader view returns (uint256) {
        return TWENTY_SEVEN_DECIMAL_NUMBER;
    }
    function mrt() external isReader view returns (uint256) {
        return 1;
    }
    function lut() external isReader view returns (uint256) {
        return lastUpdateTime;
    }
    function dgt() external isReader view returns (uint256) {
        return defaultGlobalTimeline;
    }
    function adat() external isReader view returns (uint256) {
        uint elapsed = subtract(now, lastUpdateTime);
        if (elapsed < integralPeriodSize) {
          return 0;
        }
        return subtract(elapsed, integralPeriodSize);
    }
    function tlv() external isReader view returns (uint256) {
        uint elapsed = (lastUpdateTime == 0) ? 0 : subtract(now, lastUpdateTime);
        return elapsed;
    }
}

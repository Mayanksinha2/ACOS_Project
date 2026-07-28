Weighted scoring example

Suppose MOCRA evaluates three proposals using four objectives.

Proposal

	

Profit

	

Conversion

	

Inventory

	

Traffic




Increase price

	

0.90

	

0.45

	

0.80

	

0.30




Discount campaign

	

0.50

	

0.95

	

0.90

	

0.40




Maintain price

	

0.70

	

0.70

	

0.60

	

0.60

Assume the weights are:

Objective

	

Weight




Profitability

	

0.40




Conversion rate

	

0.30




Inventory health

	

0.20




Traffic growth

	

0.10

Then:

Score(IncreasePrice)=0.40(0.90)+0.30(0.45)+0.20(0.80)+0.10(0.30)=0.685
Score(DiscountCampaign)=0.40(0.50)+0.30(0.95)+0.20(0.90)+0.10(0.40)=0.705
Score(MaintainPrice)=0.40(0.70)+0.30(0.70)+0.20(0.60)+0.10(0.60)=0.670

Since 0.705 is the highest score, Discount Campaign would be selected.

Conflict detection model

A conflict exists when two or more proposals recommend incompatible actions for the same business entity.

Define the conflict function:

Conflict(p
i
	​

,p
j
	​

)={
1,
0,
	​

if p
i
	​

 and p
j
	​

 are incompatible
otherwise
	​


Example conflicts:

Proposal A

	

Proposal B

	

Conflict?




Increase price

	

Decrease price

	

Yes




Increase inventory

	

Reduce inventory

	

Yes




Promote product

	

Increase price

	

No

Algorithm workflow

Collect all Commerce Decision Objects (CDOs) submitted through ACNP.

Extract objective values from each proposal.

Normalize objective values to a common scale.

Detect conflicts between proposals.

Compute weighted scores using the MOCRA formula.

Rank proposals by their scores.

Select the proposal with the highest score.

Store the decision outcome for learning and future optimization.

Computational complexity

Let:

n = number of proposals

m = number of objectives

The complexity of MOCRA is:

O(nm)

This complexity is efficient for practical ecommerce environments where the number of simultaneous proposals is moderate.
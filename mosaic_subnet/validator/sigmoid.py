import math


def sigmoid(x: float):
    """
    Calculates the sigmoid function of a given number.

    Parameters:
        x (float): The input number.

    Returns:
        float: The sigmoid function value of the input number.
    """
    return 1 / (1 + math.exp(-x))


def threshold_sigmoid_reward_distribution(
    score_dict: dict[int, float],
) -> dict[int, float]:
    """
    Adjusts the distribution of scores, such that the best miners are rewarded significantly more than the rest.
    This ensures that it's profitable to run a high-end model, in comparison to cheap models.

    Args:
        score_dict (dict[int, float]): A dictionary mapping miner UIDs to their scores.

    Returns:
        A dictionary mapping miner UIDs to their adjusted scores.
    """
    # Calculate the mean score
    mean_score: float = sum(score_dict.values()) / len(score_dict)

    # Set the threshold as a percentage above the mean score
    threshold_percentage = 0.2
    threshold: float = mean_score * (1 + threshold_percentage)

    steepness = 5.0  # steepness for sharper punishment

    # Set the high and low rewards
    high_reward = 1.0
    low_reward = 0.01

    # Calculate the adjusted scores using the sigmoid function
    adjusted_scores: dict[int, float] = {}
    for model_id, score in score_dict.items():
        normalized_score: float = (score - threshold) * steepness
        reward_ratio: float = sigmoid(x=normalized_score)
        adjusted_score: float = low_reward + (high_reward - low_reward) * reward_ratio
        adjusted_scores[model_id] = adjusted_score

    return adjusted_scores

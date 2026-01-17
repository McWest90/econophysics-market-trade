
import torch

def adaptive_pinn_loss(pred_volatility, true_volatility, future_volume, pred_alpha):
    """
    pred_volatility: прогноз волатильности
    pred_alpha: прогноз коэффициента alpha (сеть сама говорит, какой сейчас режим рынка)
    """
    data_loss = torch.mean((pred_volatility - true_volatility) ** 2)
    
    theoretical_vol = (future_volume + 1e-6) ** pred_alpha
    
    physics_loss = torch.mean((pred_volatility - theoretical_vol * 0.01) ** 2)
    
    alpha_penalty = torch.mean((pred_alpha - 0.44) ** 2)
    
    total_loss = data_loss + 0.5 * physics_loss + 0.1 * alpha_penalty
    return total_loss
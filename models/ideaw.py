""" IDEAW
    * Embed & Extract functions
"""

import torch
import torch.nn as nn
import yaml

from mihnet import Mihnet_s1, Mihnet_s2


class IDEAW(nn.Module):
    def __init__(self, config_path):
        super(IDEAW, self).__init__()
        self.load_config(config_path)
        self.hinet_1 = Mihnet_s1(config_path)  # for embedding msg
        self.hinet_2 = Mihnet_s2(config_path)  # for embedding locating code
        self.msg_fc = nn.Linear(self.num_bit, self.num_point)
        self.msg_fc_back = nn.Linear(self.num_point, self.num_bit)
        self.lcode_fc = nn.Linear(self.num_lc_bit, self.num_point)
        self.lcode_fc_back = nn.Linear(self.num_point, self.num_lc_bit)

    def load_config(self, config_path):
        with open(config_path) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            self.win_len = config["IDEAW"]["win_len"]
            self.n_fft = config["IDEAW"]["n_fft"]
            self.hop_len = config["IDEAW"]["hop_len"]
            self.num_bit = config["IDEAW"]["num_bit"]
            self.num_lc_bit = config["IDEAW"]["num_lc_bit"]
            self.num_point = config["IDEAW"]["num_point"]

    def stft(self, data):
        window = torch.hann_window(self.win_len).to(data.device)
        ret = torch.stft(
            input=data,
            n_fft=self.n_fft,
            hop_length=self.hop_len,
            window=window,
            return_complex=False,
        )
        return ret  # [B, F, T, C]

    def istft(self, data):
        window = torch.hann_window(self.win_len).to(data.device)
        ret = torch.istft(
            input=data,
            n_fft=self.n_fft,
            hop_length=self.hop_len,
            window=window,
            return_complex=False,
        )
        return ret

    # INN#1 Embedding & Extracting watermark message
    def embed_msg(self, audio, msg):
        audio_stft = self.stft(audio)
        msg_expand = self.msg_fc(msg)
        msg_stft = self.stft(msg_expand)
        wm_audio_stft, _ = self.enc_dec_1(audio_stft, msg_stft, rev=False)
        wm_audio = self.istft(wm_audio_stft)

        return wm_audio

    def extract_msg(self, wm_mid_stft):
        aux_signal_stft = wm_mid_stft
        _, extr_msg_expand_stft = self.enc_dec_1(wm_mid_stft, aux_signal_stft, rev=True)
        extr_msg_expand = self.istft(extr_msg_expand_stft)
        extr_msg = self.msg_fc_back(extr_msg_expand).clamp(-1, 1)
        return extr_msg

    def enc_dec_1(self, audio, msg, rev):
        audio = audio.permute(0, 3, 2, 1)  # [B, C, T, F]
        msg = msg.permute(0, 3, 2, 1)

        audio_, msg_ = self.hinet_1(audio, msg, rev)

        return audio_.permute(0, 3, 2, 1), msg_.permute(0, 3, 2, 1)

    # INN#2 Embedding & Extracting watermark locating code
    def embed_lcode(self, audio, lcode):
        audio_stft = self.stft(audio)
        lcode_expand = self.lcode_fc(lcode)
        lcode_stft = self.stft(lcode_expand)
        wm_audio_stft, _ = self.enc_dec_2(audio_stft, lcode_stft, rev=False)
        wm_audio = self.istft(wm_audio_stft)

        return wm_audio

    def extract_lcode(self, wm_audio):
        wm_audio_stft = self.stft(wm_audio)
        aux_signal_stft = wm_audio_stft
        mid_stft, extr_lcode_expand_stft = self.enc_dec_2(
            wm_audio_stft, aux_signal_stft, rev=True
        )
        extr_lcode_expand = self.istft(extr_lcode_expand_stft)
        extr_lcode = self.lcode_fc_back(extr_lcode_expand).clamp(-1, 1)
        return mid_stft, extr_lcode

    def enc_dec_2(self, audio, lcode, rev):
        audio = audio.permute(0, 3, 2, 1)  # [B, C, T, F]
        lcode = lcode.permute(0, 3, 2, 1)

        audio_, lcode_ = self.hinet_1(audio, lcode, rev)

        return audio_.permute(0, 3, 2, 1), lcode_.permute(0, 3, 2, 1)

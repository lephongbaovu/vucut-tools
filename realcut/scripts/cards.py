"""realcut · thẻ thông tin: label (nhãn chương góc trên), spec (bảng thông số kính mờ), chapter (số chương 01/02),
stat (con số lớn đếm lên), source (ghi chú/nguồn nhỏ). Toạ độ y theo tỉ lệ khung."""
import numpy as np
import textfx as T

class Cards:
    def __init__(self, cards, W, H, ratio='9:16', broll=()):
        self.W, self.H, self.ratio = W, H, ratio
        self.v = ratio == '9:16'
        self.u = W if self.v else H          # đơn vị cỡ chữ
        self.cards = list(cards)
        for b in broll:                      # nhãn B-roll tự động
            if b.get('label'):
                self.cards.append(dict(type='label', t=b['t'] + 0.15, d=max(0.8, b['d'] - 0.35), text=b['label']))
        self._c = {}

    def S(self, key, *a, **k):
        kk = (key,) + a + tuple(sorted(k.items()))
        if kk not in self._c:
            self._c[kk] = T.sprite(*a, **k)
        return self._c[kk]

    def dim_amount(self, t):
        d = 0.0
        for c in self.cards:
            if c['type'] in ('chapter', 'stat') and c['t'] <= t <= c['t'] + c['d']:
                d = max(d, T.env(t, c['t'], c['t'] + c['d'], 0.35, 0.3) * c.get('dim', 0.55))
        return d

    def draw(self, img, t):
        for c in self.cards:
            if c['t'] <= t <= c['t'] + c['d']:
                getattr(self, 'd_' + c['type'], self.d_unknown)(img, t, c)

    def d_unknown(self, img, t, c):
        pass

    def d_label(self, img, t, c):
        e = T.env(t, c['t'], c['t'] + c['d'], 0.4, 0.3)
        u = self.u; x = self.W * 0.075; y = self.H * c.get('y', 0.115 if self.v else 0.09)
        sp = self.S('lb', T.nfc(c['text']).upper(), 'light', u * 0.030, 'cream', tracking=0.28, shadow=0.6)
        T.hline(img, x, y + sp['h'] * 0.5, u * 0.05 * T.ease_out((t - c['t']) / 0.5), max(2, u * 0.0022), 'gold', e)
        T.over(img, sp, x + u * 0.07 - sp['xoff'], y, e)

    def d_spec(self, img, t, c):
        u = self.u; items = c['items']
        e = T.env(t, c['t'], c['t'] + c['d'], 0.45, 0.35)
        lsz, vsz = u * 0.026, u * 0.064
        gapv = lsz * 1.45; row_h = gapv + vsz * 1.25
        x = self.W * c.get('x', 0.09)
        w = self.W * (0.56 if self.v else 0.28)
        h = row_h * len(items) + u * 0.07
        y = self.H * c.get('y', 0.70 if self.v else 0.50) - h / 2 + u * 0.04
        T.glass(img, x - u * 0.045, y - u * 0.045, w, h, opacity=e * 0.95, radius=int(u * 0.022))
        T.hline(img, x - u * 0.045, y - u * 0.045, w * T.ease_out((t - c['t']) / 0.6), max(2, u * 0.0025), 'gold', e)
        for i, (lab, val) in enumerate(items):
            k = T.ease_out((t - c['t'] - 0.18 - i * c.get('stagger', 0.22)) / 0.45) * e
            if k <= 0:
                continue
            ls = self.S('sl', T.nfc(lab).upper(), 'medium', lsz, 'gold_soft', tracking=0.25)
            vs = self.S('sv', T.nfc(val), 'bold', T.fit_size(T.nfc(val), 'bold', vsz * 0.9, w - u * 0.06), 'cream')
            yy = y + i * row_h + (1 - k) * u * 0.02
            T.over(img, ls, x - ls['xoff'], yy + lsz - ls['base'], k)
            T.over(img, vs, x - vs['xoff'], yy + gapv + vsz * 0.95 - vs['base'], k)
            if i < len(items) - 1:
                T.hline(img, x, yy + row_h - u * 0.012, (w - u * 0.09) * k, 1, 'gold', 0.35 * k)

    def d_chapter(self, img, t, c):
        u = self.u; e = T.env(t, c['t'], c['t'] + c['d'], 0.35, 0.3)
        k = T.ease_out((t - c['t']) / 0.6)
        num = self.S('cn', c.get('num', ''), 'serif_xbi', u * 0.15, 'gold')
        txt = self.S('ct', T.nfc(c['text']).upper(), 'light', u * 0.042, 'cream', tracking=0.35)
        cy = self.H * c.get('y', 0.40)
        T.over(img, num, (self.W - num['w']) / 2, cy - num['h'] + (1 - k) * u * 0.04, e)
        lw = u * 0.16 * T.ease_out((t - c['t'] - 0.15) / 0.5)
        T.hline(img, (self.W - lw) / 2, cy + u * 0.025, lw, max(2, u * 0.0022), 'gold', e)
        T.over(img, txt, (self.W - txt['w']) / 2, cy + u * 0.055, e * T.ease_out((t - c['t'] - 0.25) / 0.4))

    def d_stat(self, img, t, c):
        u = self.u; e = T.env(t, c['t'], c['t'] + c['d'], 0.35, 0.3)
        val = str(c['value'])
        k = T.ease_out((t - c['t']) / c.get('count', 0.9))
        try:                                 # đếm lên nếu là số
            num = float(val.replace(',', '.'))
            dec = len(val.split(',')[1]) if ',' in val else (len(val.split('.')[1]) if '.' in val else 0)
            cur = num * k
            shown = (f'{cur:.{dec}f}').replace('.', ',') if dec else f'{int(round(cur)):,}'.replace(',', '.')
        except ValueError:
            shown = val
        size = u * c.get('size', 0.25)
        big = T.sprite(shown, 'serif_black', size, 'gold')
        unit = self.S('su', T.nfc(c.get('unit', '')), 'semibold', size * 0.30, 'cream') if c.get('unit') else None
        lab = self.S('sl2', T.nfc(c.get('label', '')).upper(), 'light', u * 0.034, 'cream', tracking=0.25) if c.get('label') else None
        cy = self.H * c.get('y', 0.38)
        tw = big['w'] + (unit['w'] + u * 0.02 if unit else 0)
        x = (self.W - tw) / 2
        T.over(img, big, x, cy - big['base'], e)
        if unit:
            T.over(img, unit, x + big['w'] + u * 0.02, cy - unit['base'], e)
        if lab:
            T.hline(img, (self.W - u * 0.12) / 2, cy + u * 0.04, u * 0.12, max(2, u * 0.002), 'gold', e)
            T.over(img, lab, (self.W - lab['w']) / 2, cy + u * 0.07, e * T.ease_out((t - c['t'] - 0.3) / 0.4))

    def d_source(self, img, t, c):
        u = self.u; e = T.env(t, c['t'], c['t'] + c['d'], 0.3, 0.3)
        sp = self.S('src', T.nfc(c['text']), c.get('font', 'light'), u * c.get('size', 0.024), 'cream', shadow=0.7)
        sx = (self.W - sp['w']) / 2 if c.get('align') == 'center' else (self.W * 0.075 + u * 0.07 if c.get('align') == 'label' else self.W * 0.075)
        T.over(img, sp, sx - sp['xoff'], self.H * c.get('y', 0.765 if self.v else 0.90), e * 0.85)

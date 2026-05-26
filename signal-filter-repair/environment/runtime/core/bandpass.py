"""Digital bandpass filter implementation using cascaded biquads.

Implements a simple IIR bandpass filter approximation suitable for
real-time signal processing. Uses a cascade of second-order sections
for numerical stability.

Note: This is a simplified model for demonstration purposes, using
a frequency-domain attenuation approach on windowed segments rather
than a true IIR filter. The order parameter controls rolloff steepness.
"""
import math


class BandpassFilter:
    """Applies frequency-selective filtering to signal windows.

    Attenuates frequency components outside the passband defined by
    low_cutoff and high_cutoff. The attenuation increases with filter
    order — higher order means sharper rolloff at band edges.
    """

    def __init__(self, low_cutoff, high_cutoff, sample_rate, order=4):
        """Initialize bandpass filter parameters.

        Args:
            low_cutoff: Lower passband edge in Hz.
            high_cutoff: Upper passband edge in Hz.
            sample_rate: Signal sample rate in Hz.
            order: Filter order (controls rolloff steepness).
        """
        self._low = low_cutoff
        self._high = high_cutoff
        self._fs = sample_rate
        self._order = order
        self._nyquist = sample_rate / 2.0

    def apply(self, window):
        """Apply bandpass filtering to a signal window.

        Uses DFT-based spectral filtering:
        1. Compute frequency content via DFT
        2. Apply passband gain function
        3. Reconstruct via inverse DFT

        Returns filtered window of same length as input.
        """
        n = len(window)
        if n == 0:
            return []

        # Compute DFT
        real_part = [0.0] * n
        imag_part = [0.0] * n
        for k in range(n):
            for t in range(n):
                angle = -2.0 * math.pi * k * t / n
                real_part[k] += window[t] * math.cos(angle)
                imag_part[k] += window[t] * math.sin(angle)

        # Apply frequency-domain filter
        for k in range(n):
            freq = k * self._fs / n
            if freq > self._nyquist:
                freq = self._fs - freq
            gain = self._compute_gain(freq)
            real_part[k] *= gain
            imag_part[k] *= gain

        # Inverse DFT
        filtered = [0.0] * n
        for t in range(n):
            val = 0.0
            for k in range(n):
                angle = 2.0 * math.pi * k * t / n
                val += real_part[k] * math.cos(angle) - imag_part[k] * math.sin(angle)
            filtered[t] = val / n

        return filtered

    def _compute_gain(self, freq):
        """Compute the filter gain at a given frequency.

        Uses a Butterworth-style magnitude response approximation.
        Gain is 1.0 in the passband and rolls off outside.
        """
        if freq < 1e-6:
            return 0.0

        # Normalized distances from band edges
        if freq < self._low:
            ratio = freq / self._low
            return ratio ** self._order
        elif freq > self._high:
            ratio = self._high / freq
            return ratio ** self._order
        else:
            return 1.0

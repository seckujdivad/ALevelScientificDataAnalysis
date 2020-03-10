import typing
import math

#core components of the sciplot package


class Value:
    """
    Class that holds values with their uncertainties and units. Also provides utilities for converting between percentage and absolute uncertainties as well as some formatting methods.

    NB: Python uses Banker's rounding. This class rounds upwards to resolve equidistant cases as this is the expected behaviour by A-Level physics students. This functionality can be overridden by setting round_use_internal to True.
    """
    def __init__(self, value: typing.Union[float, int, str, bytes, bytearray], uncertainty: float = 0, uncertainty_is_percentage: bool = True, units: typing.List[typing.Tuple[int, float]] = [], round_use_internal: bool = False):
        self.value: float = float(value) #enforce type
        self._uncertainty: float = uncertainty
        self._uncertainty_is_percentage: bool = uncertainty_is_percentage
        self.units = units
        self._round_use_internal: bool = round_use_internal

    def format(self, formatstring, value = None):
        """
        Format this value (or another) using the formatstring
        

        Format strings:
            ends with #: number of zeroes is number of significant figures (00#: 12345 -> 12000)
            else:
                00.00: 1.256 -> 01.26, 1 -> 01.00, -1.2 -> -01.20, 512.53 -> 12.53
                *00.0: 1.256 -> 01.3, 1 -> 01.0, -1.2 -> -01.2, 512.53 -> 512.5
                *.*:   won't change the string
                *:     won't change the string
            

            Appending e will give it as an exponent (5x10^3) where the multiplier (5) has the format string applied to it
                0.0e: 4321 -> 4.3 exponent 3

        Args:
            formatstring (str): string to format with
            value (float) = None: value to use instead of self.value (if not None)
        
        Returns:
            (multiplier: str, exponent: str or None): value post-formatting. Exponent will be None if exponent form wasn't specified by the format string
        """
        if value is None:
            value = self.value

        if formatstring.endswith('e'): #exponent mode (standard form)
            formatstring = formatstring[:-1]

            exponent = math.floor(math.log10(value))

            pivot = formatstring.find('.')
            if pivot != -1:
                exponent -= pivot
                exponent += 1
                if formatstring.startswith('*'):
                    exponent -= 1

            multiplier = value / pow(10, exponent)

            return (self.format(formatstring, multiplier)[0], str(exponent))

        else: #decimalised mode
            return_string = None
            if formatstring == '*' or formatstring == '*.*':
                return_string = str(value)
            
            elif formatstring.endswith('#'):
                significant_figures = len(formatstring) - 1

                exponent = significant_figures - 1 - math.floor(math.log10(value))

                result_value = value * pow(10, exponent)
                result_value = self.upwards_round(result_value)
                result_value /= pow(10, exponent)

                if result_value.is_integer():
                    result_value = int(result_value)
                
                return_string = str(result_value)

                required_length = len(formatstring) - 1
                return_string_sigfig = 0
                for char in return_string:
                    if (char != '.') and ((char != '0') or (return_string_sigfig > 0)):
                        return_string_sigfig += 1
                
                if return_string_sigfig < required_length:
                    chars_to_add = required_length - return_string_sigfig

                    if '.' not in return_string:
                        return_string += '.'

                    return_string += '0' * chars_to_add
            
            else:
                return_string = str(value)

                #split format string around decimal place
                if formatstring.find('.') == -1:
                    pre_decimal = formatstring
                    post_decimal = ''
                else:
                    pre_decimal = formatstring[:formatstring.find('.')]
                    post_decimal = formatstring[formatstring.find('.') + 1:]

                #interpret format string
                pre_capped = not pre_decimal.startswith('*')
                pre_size = len(pre_decimal)
                if not pre_capped:
                    pre_size -= 1

                post_capped = not post_decimal.endswith('*')
                post_size = len(post_decimal)
                if not post_capped:
                    post_size -= 1
                
                #pre rounding
                if post_capped:
                    return_string = float(return_string)
                    return_string *= pow(10, post_size)
                    return_string = self.upwards_round(return_string)
                    return_string /= pow(10, post_size)
                    return_string = str(return_string)
                
                #split value to format around decimal place
                return_pivot = return_string.find('.')
                if return_pivot == -1:
                    pre_return = return_string
                    post_return = ''
                else:
                    pre_return = return_string[:return_pivot]
                    post_return = return_string[return_pivot + 1:]
                
                if pre_size > len(pre_return):
                    pre_return = ('0' * (pre_size - len(pre_return))) + pre_return
                elif (pre_size < len(pre_return)) and pre_capped:
                    pre_return = pre_return[0 - len(pre_return) + pre_size:]
                
                if post_decimal == '':
                    post_return = ''
                elif post_size > len(post_return):
                    post_return += '0' * (post_size - len(post_return))
                elif (post_size < len(post_return)) and post_capped:
                    leading_zeroes = 0
                    
                    for i in range(len(post_return)):
                        char = post_return[i]
                        if char == '0':
                            leading_zeroes += 1
                        else:
                            break
                    
                    check_round_up = True
                    for j in range(i, len(post_return), 1):
                        if self.upwards_round(int(post_return[j]) / 10) == 0:
                            check_round_up = False
                    
                    if i < len(post_return) - 2 and post_return[i] == '9' and check_round_up:
                        leading_zeroes -= 1
                    
                    post_return = '0' * leading_zeroes + str(int(self.upwards_round(int(post_return) / pow(10, len(post_return) - post_size))))
                
                if post_return == '':
                    return_string = pre_return
                elif pre_return == '':
                    return_string = '0.{}'.format(post_return)
                else:
                    return_string = '{}.{}'.format(pre_return, post_return)

            return (return_string, None)
    
    def format_scientific(self):
        """
        Returns self.value in scientific form (standard form, uncertainty to 1 sig fig, multiplier to same number of decimal places as uncertainty)

        Returns:
            (str, str, str): multiplier, exponent, absolute uncertainty
        """
        multiplier, exponent = self.format('0.0e')
        exponent = int(exponent)
        uncertainty = self.format('0#', self.absolute_uncertainty / pow(10, exponent))[0]
        
        multiplier, exponent = self.format('0.{}e'.format('0' * int(0 - math.log10(self.percentage_uncertainty))))

        return multiplier, exponent, uncertainty
    
    def upwards_round(self, num: float):
        if self._round_use_internal:
            return round(num)
        else:
            return int(num + 0.5)

    #properties
    def _get_unc_abs(self):
        if self._uncertainty_is_percentage:
            return self._uncertainty * self.value
        else:
            return self._uncertainty
    
    def _set_unc_abs(self, value):
        self._uncertainty = value
        self._uncertainty_is_percentage = False
    
    def _get_unc_perc(self):
        if self._uncertainty_is_percentage:
            return self._uncertainty
        else:
            if self.value == 0:
                return 0
                #if self._uncertainty > 0:
                #    return float("+inf")
                #else:
                #    return float("-inf")
            else:
                return self._uncertainty / self.value
    
    def _set_unc_perc(self, value):
        self._uncertainty = value
        self._uncertainty_is_percentage = True
    
    absolute_uncertainty = property(_get_unc_abs, _set_unc_abs)
    percentage_uncertainty = property(_get_unc_perc, _set_unc_perc)
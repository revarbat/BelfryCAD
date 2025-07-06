#!/usr/bin/env python3
"""
XML Utilities

This module provides XML utilities for safe XML handling, translated from
the original TCL implementation. Uses defusedxml for secure XML parsing.

Main functions:
    expand_value: Expand XML entity references to their literal values
    escape_value: Escape special characters for XML output
    write_element: Write a self-closing XML element
    write_block_open: Write an opening XML tag
    write_block_close: Write a closing XML tag
    read_element: Read and parse XML elements from a stream

Classes:
    XmlReader: Streaming XML reader with progress callback support
"""

import html
import re
import io
from typing import Optional, Callable, Tuple, List, Union, TextIO
from defusedxml import ElementTree as ET
from xml.etree.ElementTree import Element


# Global buffer for streaming XML reading (mimics TCL's upvar behavior)
_xml_read_buffer = ""


def expand_value(val: str) -> str:
    """
    Expand XML entity references to their literal values.

    Args:
        val: String containing XML entities

    Returns:
        String with entities expanded to literal characters
    """
    # Use html.unescape for standard HTML/XML entities
    return html.unescape(val)


def escape_value(val: str) -> str:
    """
    Escape special characters for safe XML output.

    Args:
        val: String to escape

    Returns:
        String with special characters escaped
    """
    # Use html.escape for standard XML escaping
    return html.escape(val, quote=True)


def write_element(file_obj: TextIO, elem_name: str, **attrs: str) -> None:
    """
    Write a self-closing XML element to a file.

    Args:
        file_obj: File object to write to
        elem_name: Name of the XML element
        **attrs: Element attributes as keyword arguments
    """
    output = f"<{escape_value(elem_name)}"

    for key, val in attrs.items():
        if val:  # Only include non-empty values
            output += f' {escape_value(key)}="{escape_value(val)}"'

    output += " />"
    file_obj.write(output + "\n")


def write_block_open(file_obj: TextIO, elem_name: str, **attrs: str) -> None:
    """
    Write an opening XML tag to a file.

    Args:
        file_obj: File object to write to
        elem_name: Name of the XML element
        **attrs: Element attributes as keyword arguments
    """
    output = f"<{escape_value(elem_name)}"

    for key, val in attrs.items():
        if val:  # Only include non-empty values
            output += f' {escape_value(key)}="{escape_value(val)}"'

    output += ">"
    file_obj.write(output + "\n")


def write_block_close(file_obj: TextIO, elem_name: str) -> None:
    """
    Write a closing XML tag to a file.

    Args:
        file_obj: File object to write to
        elem_name: Name of the XML element
    """
    output = f"</{escape_value(elem_name)}>"
    file_obj.write(output + "\n")


class XmlReader:
    """
    Streaming XML reader that mimics the behavior of the TCL xmlutil_read_element.

    This class provides a streaming XML parser that can handle large files
    and provides progress callbacks during parsing.
    """

    def __init__(self, file_obj: TextIO,
                 progress_callback: Optional[Callable[[int], None]] = None):
        """
        Initialize the XML reader.

        Args:
            file_obj: File object to read from
            progress_callback: Optional callback function for progress updates
        """
        self.file_obj = file_obj
        self.progress_callback = progress_callback
        self.read_buffer = ""
        self.read_size = 1024

    def read_element(self) -> Tuple[str, Union[str, List[str]]]:
        """
        Read and parse the next XML element from the stream.

        Returns:
            Tuple of (element_type, content) where:
            - element_type: "EOF", "TEXT", "ERROR", or tag name like "<tagname>"
            - content: The text content, error message, or list of
              attributes

        Raises:
            ValueError: For malformed XML
        """
        while True:
            pos = self.read_buffer.find("<")
            rblen = len(self.read_buffer)

            # Read more data if we don't have a '<' and haven't reached EOF
            while pos == -1 and not self._is_eof():
                tmp_buf = self.file_obj.read(self.read_size)
                if self.progress_callback:
                    current_pos = self.file_obj.tell()
                    self.progress_callback(current_pos)

                self.read_buffer += tmp_buf
                pos = self.read_buffer.find("<", rblen - 1)
                rblen = len(self.read_buffer)

            if pos == -1:
                # Text at end of file
                if not self.read_buffer:
                    return ("EOF", "")
                else:
                    text = expand_value(self.read_buffer)
                    self.read_buffer = ""
                    return ("TEXT", text)

            elif pos > 0:
                # Text before next element
                text = self.read_buffer[:pos]
                self.read_buffer = self.read_buffer[pos:].lstrip()
                return ("TEXT", expand_value(text))

            # First char is '<', so this is an element or special content
            if self.read_buffer.startswith("<?xml"):
                # Skip XML header
                self._skip_until("?>", 5)
                continue

            elif self.read_buffer.startswith("<!--"):
                # Skip comment
                self._skip_until("-->", 4)
                continue

            else:
                # This is an element
                break

        # Parse element
        return self._parse_element()

    def _is_eof(self) -> bool:
        """Check if we've reached end of file."""
        try:
            current_pos = self.file_obj.tell()
            # Try to read a small amount to check if we're at EOF
            test_read = self.file_obj.read(1)
            if test_read:
                # Put the character back
                self.file_obj.seek(current_pos)
                return False
            else:
                return True
        except (OSError, io.UnsupportedOperation):
            # For some file-like objects, we can't seek
            return False

    def _skip_until(self, delimiter: str, start_offset: int) -> None:
        """Skip content until delimiter is found."""
        self.read_buffer = self.read_buffer[start_offset:]
        pos = self.read_buffer.find(delimiter)
        rblen = len(self.read_buffer)

        while pos == -1 and not self._is_eof():
            tmp_buf = self.file_obj.read(self.read_size)
            if self.progress_callback:
                current_pos = self.file_obj.tell()
                self.progress_callback(current_pos)

            self.read_buffer += tmp_buf
            pos = self.read_buffer.find(delimiter, rblen)
            rblen = len(self.read_buffer)

        if pos == -1:
            raise ValueError(f"Unterminated {delimiter} at end of file")

        self.read_buffer = self.read_buffer[pos + len(delimiter):]

    def _parse_element(self) -> Tuple[str, List[str]]:
        """Parse a complete XML element."""
        # Find the end of the element
        pos = self.read_buffer.find(">")
        rblen = len(self.read_buffer)

        while pos == -1 and not self._is_eof():
            tmp_buf = self.file_obj.read(self.read_size)
            if self.progress_callback:
                current_pos = self.file_obj.tell()
                self.progress_callback(current_pos)

            self.read_buffer += tmp_buf
            pos = self.read_buffer.find(">", rblen - 1)
            rblen = len(self.read_buffer)

        if pos == -1:
            raise ValueError("Unterminated element at end of file")

        # Extract element string
        elem_str = self.read_buffer[:pos + 1]
        self.read_buffer = self.read_buffer[pos + 1:].lstrip()

        # Parse element using regex (similar to TCL version)
        match = re.match(r'^<(/?[a-zA-Z_][a-zA-Z0-9_:-]*)\s*([^>]*>)$',
                         elem_str, re.IGNORECASE)

        if not match:
            raise ValueError("Malformed tag")

        tag_name = match.group(1).lower()
        attr_str = match.group(2)[:-1]  # Remove the final '>'

        # Parse attributes
        attrs = []
        attr_str = attr_str.strip()

        while attr_str and not attr_str.endswith("/"):
            # Try quoted attribute value
            quoted_pattern = (r'^\s*([a-zA-Z_][a-zA-Z0-9_:-]*)='
                              r'[\'"]([^\'"]*)[\'"](.*)$')
            quoted_match = re.match(quoted_pattern, attr_str, re.IGNORECASE)
            if quoted_match:
                attr_name = quoted_match.group(1)
                attr_value = quoted_match.group(2)
                attr_str = quoted_match.group(3).strip()
            else:
                # Try unquoted attribute value
                unquoted_pattern = (r'^\s*([a-zA-Z_][a-zA-Z0-9_:-]*)='
                                    r'([^\s]*)(.*)$')
                unquoted_match = re.match(unquoted_pattern, attr_str,
                                          re.IGNORECASE)
                if unquoted_match:
                    attr_name = unquoted_match.group(1)
                    attr_value = unquoted_match.group(2)
                    attr_str = unquoted_match.group(3).strip()
                else:
                    # Boolean attribute (no value)
                    bool_pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_:-]*)(.*)$'
                    bool_match = re.match(bool_pattern, attr_str,
                                          re.IGNORECASE)
                    if bool_match:
                        attr_name = bool_match.group(1)
                        attr_value = attr_name  # TCL behavior: value = name
                        attr_str = bool_match.group(2).strip()
                    else:
                        raise ValueError("Malformed attribute")

            attrs.append(expand_value(attr_name))
            attrs.append(expand_value(attr_value))

        # Handle self-closing tags
        if attr_str.endswith("/"):
            tag_name += "/"

        return (f"<{tag_name}>", attrs)


def read_element(file_obj: TextIO,
                 progress_callback: Optional[Callable[[int], None]] = None
                 ) -> Tuple[str, Union[str, List[str]]]:
    """
    Read and parse an XML element from a file stream (legacy function).

    This function provides the same interface as the TCL
    xmlutil_read_element for backward compatibility.

    Args:
        file_obj: File object to read from
        progress_callback: Optional callback function for progress updates

    Returns:
        Tuple of (element_type, content) where:
        - element_type: "EOF", "TEXT", "ERROR", or tag name like "<tagname>"
        - content: The text content, error message, or list of attributes
    """
    # Use a global reader instance to maintain state (mimics TCL's upvar)
    global _xml_reader_instance

    cache_attr = '_reader_cache'
    if (not hasattr(read_element, cache_attr) or
            file_obj not in getattr(read_element, cache_attr)):
        if not hasattr(read_element, cache_attr):
            setattr(read_element, cache_attr, {})
        getattr(read_element, cache_attr)[file_obj] = XmlReader(
            file_obj, progress_callback)

    reader = getattr(read_element, cache_attr)[file_obj]

    try:
        return reader.read_element()
    except ValueError as e:
        return ("ERROR", str(e))


def parse_xml_file(file_path: str) -> Element:
    """
    Parse an XML file using defusedxml for security.

    Args:
        file_path: Path to the XML file

    Returns:
        Root element of the parsed XML

    Raises:
        ParseError: If the XML is malformed
        FileNotFoundError: If the file doesn't exist
    """
    return ET.parse(file_path).getroot()


def parse_xml_string(xml_string: str) -> Element:
    """
    Parse an XML string using defusedxml for security.

    Args:
        xml_string: XML content as a string

    Returns:
        Root element of the parsed XML

    Raises:
        ParseError: If the XML is malformed
    """
    return ET.fromstring(xml_string)


# Convenience functions for common XML operations
def create_element(tag: str, text: Optional[str] = None,
                   **attrs: str) -> Element:
    """
    Create an XML element with optional text and attributes.

    Args:
        tag: Tag name
        text: Optional text content
        **attrs: Element attributes

    Returns:
        New XML element
    """
    elem = ET.Element(tag, attrs)
    if text is not None:
        elem.text = text
    return elem


def element_to_string(element: Element, encoding: str = 'unicode') -> str:
    """
    Convert an XML element to a string.

    Args:
        element: XML element to convert
        encoding: Output encoding ('unicode' for string, 'utf-8' for bytes)

    Returns:
        String representation of the element
    """
    return ET.tostring(element, encoding=encoding, method='xml')


# vim: set ts=4 sw=4 nowrap expandtab:

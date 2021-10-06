from xml.etree import ElementTree
import logging

LOGGER = logging.getLogger(__name__)


def get_bounding_box_srs(service, content):
    root = ElementTree.fromstring(content)
    tag = root.tag.split('}')
    layer_tag = 'Layer'
    bound_tag = 'BoundingBox'
    name_tag = 'Name'
    if len(tag) > 1:
        layer_tag = tag[0] + '}' + layer_tag
        bound_tag = tag[0] + '}' + bound_tag
        name_tag = tag[0] + '}' + name_tag

    layers = root.iter(layer_tag)
    out = {}

    for layer in layers:
        if layer.find(name_tag) is None:
            continue
        if layer.find(name_tag).text == service:
            out['srs'] = layer.find(bound_tag).get('CRS')
            out['bbox'] = '{},{},{},{}'.format(
                layer.find(bound_tag).get('minx'),
                layer.find(bound_tag).get('miny'),
                layer.find(bound_tag).get('maxx'),
                layer.find(bound_tag).get('maxy'),
            )

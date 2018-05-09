# coding=utf-8
"""Context Cache Model."""

from django.utils.translation import ugettext_lazy as _

from django.contrib.gis.db import models

from geocontext.models.context_service_registry import ContextServiceRegistry


class ContextCache(models.Model):
    """Context Cache Model Class."""

    name = models.CharField(
        help_text=_('Name of Cache Context.'),
        blank=False,
        null=False,
        max_length=200,
    )

    source_uri = models.CharField(
        help_text=_('Source URI of the Context.'),
        blank=False,
        null=False,
        max_length=1000,
    )

    geometry_linestring = models.LineStringField(
        help_text=_('The line geometry of the context.'),
        blank=True,
        null=True,
        dim=2
    )

    geometry_multi_linestring = models.MultiLineStringField(
        help_text=_('The multi line geometry of the context.'),
        blank=True,
        null=True,
        dim=2
    )

    geometry_polygon = models.PolygonField(
        help_text=_('The polygon geometry of the context.'),
        blank=True,
        null=True,
        dim=2
    )

    geometry_multi_polygon = models.MultiPolygonField(
        help_text=_('The multi polygon geometry of the context.'),
        blank=True,
        null=True,
        dim=2
    )

    geometry_linestring_3d = models.LineStringField(
        help_text=_('The 3d line geometry of the context.'),
        blank=True,
        null=True,
        dim=3
    )

    geometry_multi_linestring_3d = models.MultiLineStringField(
        help_text=_('The 3d multi line geometry of the context.'),
        blank=True,
        null=True,
        dim=3
    )

    geometry_polygon_3d = models.PolygonField(
        help_text=_('The 3d polygon geometry of the context.'),
        blank=True,
        null=True,
        dim=3
    )

    geometry_multi_polygon_3d = models.MultiPolygonField(
        help_text=_('The 3d multi polygon geometry of the context.'),
        blank=True,
        null=True,
        dim=3
    )

    service_registry = models.ForeignKey(
        ContextServiceRegistry,
        help_text=_('Service registry where the context comes from'),
        on_delete=models.CASCADE
    )

    value = models.CharField(
        help_text=_('The value of the context.'),
        blank=False,
        null=False,
        max_length=200,
    )

    expired_time = models.DateTimeField(
        help_text=_('When the cache expired.'),
        blank=False,
        null=False
    )

    def set_geometry_field(self, geometry):
        """Set geometry field based on the type

        :param geometry: The geometry.
        :type geometry: GEOSGeometry
        """
        if geometry.geom_type in ['LineString', 'LinearRing']:
            if geometry.hasz:
                self.geometry_linestring_3d = geometry
            else:
                self.geometry_linestring = geometry
        elif geometry.geom_type == 'Polygon':
            if geometry.hasz:
                self.geometry_polygon_3d = geometry
            else:
                self.geometry_polygon = geometry
        elif geometry.geom_type == 'MultiLineString':
            if geometry.hasz:
                self.geometry_multi_linestring_3d = geometry
            else:
                self.geometry_multi_linestring = geometry
        elif geometry.geom_type == 'MultiPolygon':
            if geometry.hasz:
                self.geometry_multi_polygon_3d = geometry
            else:
                self.geometry_multi_polygon = geometry

    @property
    def geometry(self):
        """Attribute for geometry

        :return: The geometry of the cache
        :rtype: GEOSGeometry
        """
        if self.geometry_linestring:
            return self.geometry_linestring
        elif self.geometry_polygon:
            return self.geometry_polygon
        elif self.geometry_multi_linestring:
            return self.geometry_multi_linestring
        elif self.geometry_multi_polygon:
            return self.geometry_multi_polygon
        elif self.geometry_linestring_3d:
            return self.geometry_linestring_3d
        elif self.geometry_polygon_3d:
            return self.geometry_polygon_3d
        elif self.geometry_multi_linestring_3d:
            return self.geometry_multi_linestring_3d
        elif self.geometry_multi_polygon_3d:
            return self.geometry_multi_polygon_3d
        else:
            return None
